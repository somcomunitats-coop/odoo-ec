import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)
from odoo.addons.energy_project.config import PROJECT_STATE_ACTIVE

from ..config import DISTRIBUTION_STATE_ACTIVE, DISTRIBUTION_STATE_PROCESS

# Constants for contract generation wizard
SALE_ORDER_STATE_DRAFT = "draft"
PAYMENT_TYPE_INBOUND = "inbound"
MAIN_LINE_FLAG = True

logger = logging.getLogger(__name__)


class ContractGenerationWizard(models.TransientModel):
    """
    Contract Generation Wizard

    This wizard handles the generation of contracts for a self-consumption project,
    including sale order confirmation, contract setup, and project activation.

    Features:
    - Sale order confirmation with payment mode setup
    - Contract line configuration and description setup
    - Distribution table activation
    - Project state management
    - Comprehensive validation and error handling
    """

    _name = "energy_selfconsumption.contract_generation.wizard"
    _description = "Contract Generation Wizard"

    # Project relationship
    selfconsumption_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption",
        string="Self-consumption Project",
        readonly=True,
        required=True,
        help="Self-consumption project for contract generation",
    )

    # Contract configuration
    start_date = fields.Date(
        string="Contract Start Date",
        help="Starting date for the contracts and invoicing",
        required=True,
        default=fields.Date.today(),
    )

    payment_mode = fields.Many2one(
        "account.payment.mode",
        string="Payment Mode",
        required=True,
        default=lambda self: self._default_payment_mode(),
        help="Payment mode to be used for the contracts",
    )

    # Computed fields for validation
    draft_sale_orders_count = fields.Integer(
        string="Draft Sale Orders",
        compute="_compute_draft_sale_orders_count",
        help="Number of draft sale orders that will be processed",
    )

    distribution_table_ready = fields.Boolean(
        string="Distribution Table Ready",
        compute="_compute_distribution_table_ready",
        help="Whether there is a distribution table ready for activation",
    )

    def _default_payment_mode(self):
        """
        Get default payment mode for the current company

        Returns:
            payment_mode: Default inbound payment mode for the company
        """
        try:
            return self.env["account.payment.mode"].search(
                [
                    ("company_id", "=", self.env.company.id),
                    ("payment_type", "=", PAYMENT_TYPE_INBOUND),
                ],
                limit=1,
            )
        except Exception as e:
            logger.warning(f"Error getting default payment mode: {e}")
            return False

    @api.depends("selfconsumption_id")
    def _compute_draft_sale_orders_count(self):
        """
        Compute the number of draft sale orders
        """
        for wizard in self:
            if wizard.selfconsumption_id:
                draft_orders = wizard._get_impacted_sale_orders()
                wizard.draft_sale_orders_count = len(draft_orders)
            else:
                wizard.draft_sale_orders_count = 0

    @api.depends("selfconsumption_id")
    def _compute_distribution_table_ready(self):
        """
        Compute whether distribution table is ready for activation
        """
        for wizard in self:
            if wizard.selfconsumption_id:
                wizard.distribution_table_ready = (
                    wizard._has_distribution_table_in_process()
                )
            else:
                wizard.distribution_table_ready = False

    def _get_impacted_sale_orders(self):
        """
        Get sale orders that will be impacted by contract generation

        Returns:
            sale_orders: Recordset of draft sale orders for the project
        """
        if not self.selfconsumption_id:
            return self.env["sale.order"]

        try:
            sale_orders = self.selfconsumption_id.get_sale_orders()
            return sale_orders.filtered(lambda so: so.state == SALE_ORDER_STATE_DRAFT)
        except Exception as e:
            logger.error(f"Error getting impacted sale orders: {e}")
            return self.env["sale.order"]

    def _has_distribution_table_in_process(self):
        """
        Check if there is a distribution table ready for activation

        Returns:
            bool: True if distribution table is ready, False otherwise
        """
        if not self.selfconsumption_id:
            return False

        try:
            distribution_table = (
                self.selfconsumption_id.distribution_table_ids.filtered_domain(
                    [("state", "=", DISTRIBUTION_STATE_PROCESS)]
                )
            )
            return bool(distribution_table)
        except Exception as e:
            logger.error(f"Error checking distribution table: {e}")
            return False

    def _get_distribution_table_in_process(self):
        """
        Get the distribution table that is in process state

        Returns:
            distribution_table: Distribution table record

        Raises:
            ValidationError: If no distribution table is found
        """
        distribution_table = (
            self.selfconsumption_id.distribution_table_ids.filtered_domain(
                [("state", "=", DISTRIBUTION_STATE_PROCESS)]
            )
        )

        if not distribution_table:
            raise ValidationError(
                _("There is no distribution table in process of activation.")
            )

        return distribution_table

    def action_generate_contracts(self):
        """
        Generate contracts for the self-consumption project

        Main method that orchestrates the entire contract generation process:
        1. Validates prerequisites
        2. Confirms sale orders
        3. Sets up contracts
        4. Activates project and distribution table

        Returns:
            bool: True if contracts were generated successfully

        Raises:
            ValidationError: If validation fails
            UserError: If errors occur during processing
        """
        self.ensure_one()

        try:
            # Validate prerequisites
            self._validate_contract_generation()

            # Get distribution table
            distribution_table = self._get_distribution_table_in_process()

            # Process sale orders and generate contracts
            contracts_created = self._process_sale_orders(distribution_table)

            # Activate project and distribution table
            self._activate_project_and_distribution()

            logger.info(
                f"Successfully generated {contracts_created} contracts for project {self.selfconsumption_id.id}"
            )

            return True

        except Exception as e:
            logger.error(f"Error generating contracts: {e}")
            if isinstance(e, (ValidationError, UserError)):
                raise
            else:
                raise UserError(_("Error generating contracts. Please try again."))

    def _validate_contract_generation(self):
        """
        Validate prerequisites for contract generation

        Raises:
            ValidationError: If validation fails
        """
        if not self.selfconsumption_id:
            raise ValidationError(_("No self-consumption project specified"))

        if not self.payment_mode:
            raise ValidationError(_("Payment mode is required for contract generation"))

        if not self.start_date:
            raise ValidationError(_("Start date is required for contract generation"))

        # Check if there are draft sale orders to process
        draft_orders = self._get_impacted_sale_orders()
        if not draft_orders:
            raise ValidationError(_("No draft sale orders found to process"))

        # Check distribution table
        if not self._has_distribution_table_in_process():
            raise ValidationError(
                _("There is no distribution table in process of activation.")
            )

    def _process_sale_orders(self, distribution_table):
        """
        Process all draft sale orders and generate contracts

        Args:
            distribution_table: Distribution table for contract setup

        Returns:
            int: Number of contracts created
        """
        draft_orders = self._get_impacted_sale_orders()
        contracts_created = 0

        for sale_order in draft_orders:
            try:
                contract = self._process_single_sale_order(
                    sale_order, distribution_table
                )
                if contract:
                    contracts_created += 1
                    logger.info(f"Contract created for sale order {sale_order.id}")
            except Exception as e:
                logger.error(f"Error processing sale order {sale_order.id}: {e}")
                raise UserError(
                    _(
                        "Error processing sale order {order}. Please check the configuration."
                    ).format(order=sale_order.name)
                )

        return contracts_created

    def _process_single_sale_order(self, sale_order, distribution_table):
        """
        Process a single sale order and generate contract

        Args:
            sale_order: Sale order to process
            distribution_table: Distribution table for setup

        Returns:
            contract: Generated contract record
        """
        # 1. Confirm sale order with extra configuration
        contract = self._confirm_sale_order(sale_order)

        # 2. Setup contract line description
        # self._setup_contract_line_description(contract, distribution_table)

        # 3. Setup main contract line
        self._setup_main_contract_line(contract)

        # 4. Activate contract
        self._activate_contract(contract)

        return contract

    def _confirm_sale_order(self, sale_order):
        """
        Confirm sale order with payment mode and commitment date

        Args:
            sale_order: Sale order to confirm

        Returns:
            contract: Generated contract from sale order
        """
        so_extra = {
            "commitment_date": self.start_date,
            "payment_mode_id": self.payment_mode.id,
        }

        with sale_order_utils(self.env, sale_order) as component:
            contract = component.confirm(**so_extra)

        return contract

    # def _setup_contract_line_description(self, contract, distribution_table):

    def _setup_main_contract_line(self, contract):
        """
        Setup the main contract line flag

        Args:
            contract: Contract to setup
        """
        if contract.contract_line_ids:
            contract.contract_line_ids[0].write({"main_line": MAIN_LINE_FLAG})

    def _activate_contract(self, contract):
        """
        Activate the contract with the specified start date

        Args:
            contract: Contract to activate
        """
        with contract_utils(self.env, contract) as component:
            component.activate(self.start_date)

    def _activate_project_and_distribution(self):
        """
        Activate the project and distribution table
        """
        # Activate project
        self.selfconsumption_id.write(
            {"payment_mode_id": self.payment_mode.id, "state": PROJECT_STATE_ACTIVE}
        )

        # Activate distribution table
        self.selfconsumption_id.distribution_table_state(
            DISTRIBUTION_STATE_PROCESS, DISTRIBUTION_STATE_ACTIVE
        )

    # Utility methods
    def get_wizard_summary(self):
        """
        Get summary information about the wizard

        Returns:
            dict: Summary information
        """
        self.ensure_one()

        return {
            "project_name": self.selfconsumption_id.name,
            "start_date": self.start_date,
            "payment_mode": self.payment_mode.name if self.payment_mode else "Not set",
            "draft_orders_count": self.draft_sale_orders_count,
            "distribution_table_ready": self.distribution_table_ready,
        }

    def validate_wizard_data(self):
        """
        Validate wizard data before proceeding

        Returns:
            bool: True if validation passes

        Raises:
            ValidationError: If validation fails
        """
        try:
            self._validate_contract_generation()
            return True
        except ValidationError:
            raise

    def preview_contract_generation(self):
        """
        Preview contract generation without executing it

        Returns:
            dict: Preview information
        """
        self.ensure_one()

        draft_orders = self._get_impacted_sale_orders()

        preview_data = {
            "project_name": self.selfconsumption_id.name,
            "contracts_to_create": len(draft_orders),
            "sale_orders": [
                {
                    "name": order.name,
                    "partner": order.partner_id.name,
                    "amount_total": order.amount_total,
                }
                for order in draft_orders
            ],
            "start_date": self.start_date,
            "payment_mode": self.payment_mode.name if self.payment_mode else "Not set",
        }

        return preview_data
