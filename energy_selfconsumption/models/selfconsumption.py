import base64
import logging
from datetime import datetime, timedelta
from io import StringIO

import chardet
import pandas as pd
from dateutil.relativedelta import relativedelta
from stdnum.es import cups, referenciacatastral
from stdnum.exceptions import (
    InvalidChecksum,
    InvalidComponent,
    InvalidFormat,
    InvalidLength,
)

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)
from odoo.addons.energy_communities_service_invoicing.utils import (
    get_existing_pack_contract,
)
from odoo.addons.energy_project.config import (
    PROJECT_STATE_ACTIVATION,
    PROJECT_STATE_ACTIVE,
    PROJECT_STATE_DRAFT,
)

from ..config import (
    CAU_LENGTH_24,
    CAU_LENGTH_26,
    CAU_SEPARATOR,
    CIL_LENGTH_23,
    CIL_LENGTH_25,
    CUPS_LENGTH_20,
    CUPS_LENGTH_22,
    DISTRIBUTION_STATE_ACTIVE,
    DISTRIBUTION_STATE_CANCELLED,
    DISTRIBUTION_STATE_PROCESS,
    DISTRIBUTION_STATE_VALIDATED,
    INSCRIPTION_STATE_ACTIVE,
    INSCRIPTION_STATE_CHANGE,
    LAST_DIGITS_COUNT,
    RECURRING_INVOICING_TYPE_POSTPAID,
    RECURRING_INVOICING_TYPE_PREPAID,
    SELFCONSUMPTION_CONF_STATE_ACTIVE,
    SELFCONSUMPTION_CONF_STATE_DEFAULT_VALUE,
    SELFCONSUMPTION_CONF_STATE_INACTIVE,
    SELFCONSUMPTION_CONF_STATE_VALUES,
    SELFCONSUMPTION_DEFAULT_INVOICING_MODE,
    SELFCONSUMPTION_DEFAULT_PARTICIPATIONS,
    SELFCONSUMPTION_INVOICING_MODE_POWER_ACQUIRED,
    SELFCONSUMPTION_INVOICING_MODE_VALUES,
)

_logger = logging.getLogger(__name__)


class Selfconsumption(models.Model):
    """
    Self-consumption Energy Project Model

    This model manages energy self-consumption projects including:
    - Project configuration and validation
    - Distribution tables management
    - Inscriptions handling
    - Contract generation and management
    - Invoicing processes
    """

    _name = "energy_selfconsumption.selfconsumption"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _inherits = {
        "energy_project.project": "project_id",
    }
    _description = "Self-consumption Energy Project"

    _sql_constraints = [
        (
            "unique_code",
            "UNIQUE(code)",
            _("A project with this CAU already exists."),
        ),
    ]

    # Compute methods
    def _compute_distribution_table_count(self):
        """Calculate the number of distribution tables for each record"""
        for record in self:
            record.distribution_table_count = len(record.distribution_table_ids)

    def _compute_inscription_count(self):
        """Calculate the number of inscriptions for each record"""
        for record in self:
            record.inscription_count = len(record.inscription_ids)

    def _compute_contract_count(self):
        """Calculate the number of active contracts for each record"""
        for record in self:
            related_contracts = self.env["contract.contract"].search_count(
                [("project_id", "=", record.id), ("status", "=", "in_progress")]
            )
            record.contracts_count = related_contracts

    def _compute_sale_orders_count(self):
        """Calculate the number of sale orders for each record"""
        for record in self:
            sale_orders = self.get_sale_orders()
            record.sale_orders_count = len(sale_orders)

    def _compute_current_distribution_table(self):
        """Get the currently active distribution table"""
        for record in self:
            table_in_active = record.distribution_table_ids.filtered_domain(
                [("state", "=", DISTRIBUTION_STATE_ACTIVE)]
            )
            if table_in_active:
                record.current_distribution_table = table_in_active
            else:
                record.current_distribution_table = False

    # Field definitions
    project_id = fields.Many2one(
        "energy_project.project", required=True, ondelete="cascade"
    )
    code = fields.Char(string="CAU", help="Self-consumption Authorization Code")
    cil = fields.Char(
        string="CIL", help="Production facility code for liquidation purposes"
    )
    owner_id = fields.Many2one(
        "res.partner",
        string="Owner",
        required=True,
        default=lambda self: self.env.company.partner_id,
        help="Owner of the self-consumption project",
    )
    power = fields.Float(string="Power (kW)", help="Total power capacity in kilowatts")
    distribution_table_ids = fields.One2many(
        "energy_selfconsumption.distribution_table",
        "selfconsumption_project_id",
        readonly=True,
        help="Distribution tables associated with this project",
    )
    report_distribution_table = fields.Many2one(
        "energy_selfconsumption.distribution_table",
        help="Distribution table used for report generation",
    )
    current_distribution_table = fields.Many2one(
        "energy_selfconsumption.distribution_table",
        compute=_compute_current_distribution_table,
        readonly=True,
        store=False,
        help="Currently active distribution table",
    )
    distribution_table_count = fields.Integer(
        compute=_compute_distribution_table_count, help="Number of distribution tables"
    )
    inscription_ids = fields.One2many(
        "energy_selfconsumption.inscription_selfconsumption",
        "selfconsumption_project_id",
        readonly=True,
        help="Inscriptions for this self-consumption project",
    )
    inscription_count = fields.Integer(
        compute=_compute_inscription_count, help="Number of inscriptions"
    )
    contracts_count = fields.Integer(
        compute=_compute_contract_count, help="Number of active contracts"
    )
    sale_orders_count = fields.Integer(
        compute=_compute_sale_orders_count, help="Number of sale orders"
    )
    invoicing_mode = fields.Selection(
        SELFCONSUMPTION_INVOICING_MODE_VALUES,
        string="Invoicing Mode",
        help="Method used for invoicing this project",
    )
    payment_mode_id = fields.Many2one(
        "account.payment.mode",
        string="Payment mode",
        help="Default payment mode for this project",
    )
    product_id = fields.Many2one(
        "product.product", string="Product", help="Product associated with this project"
    )
    contract_template_id = fields.Many2one(
        "contract.template",
        string="Contract Template",
        related="product_id.property_contract_template_id",
        help="Template used for contract generation",
    )
    supplier_id = fields.Many2one(
        "energy_project.supplier",
        string="Energy Supplier",
        help="Select the associated Energy Supplier",
    )
    cadastral_reference = fields.Char(
        string="Cadastral reference",
        help="Official cadastral reference for the project location",
    )
    conf_cadastral_reference_readonly = fields.Boolean(
        "Cadastral reference readonly",
        default=True,
        help="Make the cadastral reference field readonly",
    )
    conf_state = fields.Selection(
        SELFCONSUMPTION_CONF_STATE_VALUES,
        string="Activate Registration Form",
        default=SELFCONSUMPTION_CONF_STATE_DEFAULT_VALUE,
        required=True,
        help="Controls whether the registration form is active",
    )
    conf_participation_ids = fields.One2many(
        "energy_selfconsumptions.participation",
        "project_id",
        string="Participation",
        help="Available participation options for this project",
    )
    conf_used_in_selfconsumption = fields.Boolean(
        "Show used in selfconsumption", help="Display usage in self-consumption field"
    )
    conf_vulnerability_situation = fields.Boolean(
        "Show vulnerability situation", help="Display vulnerability situation field"
    )
    conf_bank_details = fields.Boolean(
        "Request bank details",
        default=True,
        help="Select when you want to make the payment by bank transfer. If not requested, the payment must be made by bank transfer by the member.",
    )
    conf_url_form = fields.Char(string="URL", help="URL for the registration form")

    # Validation methods
    def _validate_cups_code(self, code, code_type, cups_length, total_length):
        """
        Generic method to validate CUPS-based codes (CAU/CIL)

        Args:
            code (str): The code to validate
            code_type (str): Type of code ('CAU' or 'CIL') for error messages
            cups_length (int): Expected CUPS length (20 or 22)
            total_length (int): Expected total code length

        Returns:
            str: The last digits after CUPS validation

        Raises:
            ValidationError: If validation fails
        """
        try:
            cups.validate(code[:cups_length])
        except InvalidLength:
            error_message = _(
                "Invalid {code_type}: The first characters related to CUPS are incorrect. The length is incorrect."
            ).format(code_type=code_type)
            raise ValidationError(error_message)
        except InvalidComponent:
            error_message = _(
                "Invalid {code_type}: The CUPS does not start with 'ES'."
            ).format(code_type=code_type)
            raise ValidationError(error_message)
        except InvalidFormat:
            error_message = _(
                "Invalid {code_type}: The CUPS has an incorrect format."
            ).format(code_type=code_type)
            raise ValidationError(error_message)
        except InvalidChecksum:
            error_message = _(
                "Invalid {code_type}: The checksum of the CUPS is incorrect."
            ).format(code_type=code_type)
            raise ValidationError(error_message)

        return code[cups_length:]

    @api.constrains("code")
    def _check_valid_code(self):
        """
        Validate CAU (Self-consumption Authorization Code) format.

        The validation checks:
        1. First 20 or 22 digits correspond to valid CUPS
        2. Character after CUPS is 'A'
        3. Last 3 characters are numbers
        4. Total length is 24 or 26 characters
        """
        for record in self:
            if not record.code:
                continue

            code_length = len(record.code)

            # Determine CUPS length based on total code length
            if code_length == CAU_LENGTH_24:
                cups_length = CUPS_LENGTH_20
            elif code_length == CAU_LENGTH_26:
                cups_length = CUPS_LENGTH_22
            else:
                error_message = _("Invalid CAU: The length is not correct")
                raise ValidationError(error_message)

            # Validate CUPS portion and get remaining digits
            last_digits = self._validate_cups_code(
                record.code, "CAU", cups_length, code_length
            )

            # Check if the character after CUPS is 'A'
            if not last_digits.startswith(CAU_SEPARATOR):
                error_message = _("Invalid CAU: The character after CUPS is not A")
                raise ValidationError(error_message)

            # Check if the last 3 characters are numbers
            if not last_digits[-LAST_DIGITS_COUNT:].isdigit():
                error_message = _("Invalid CAU: Last 3 digits are not numbers")
                raise ValidationError(error_message)

    @api.constrains("cil")
    def _check_valid_cil(self):
        """
        Validate CIL (Production facility code for liquidation) format.

        The validation checks:
        1. First 20 or 22 digits correspond to valid CUPS
        2. Last 3 characters are numbers
        3. Total length is 23 or 25 characters
        """
        for record in self:
            if not record.cil:
                continue

            code_length = len(record.cil)

            # Determine CUPS length based on total code length
            if code_length == CIL_LENGTH_23:
                cups_length = CUPS_LENGTH_20
            elif code_length == CIL_LENGTH_25:
                cups_length = CUPS_LENGTH_22
            else:
                error_message = _("Invalid CIL: The length is not correct")
                raise ValidationError(error_message)

            # Validate CUPS portion and get remaining digits
            # Note: Using record.code instead of record.cil seems to be a bug in original code
            # This should be fixed to use record.cil
            last_digits = self._validate_cups_code(
                record.cil, "CIL", cups_length, code_length
            )

            # Check if the last 3 characters are numbers
            if not last_digits[-LAST_DIGITS_COUNT:].isdigit():
                error_message = _("Invalid CIL: Last 3 digits are not numbers")
                raise ValidationError(error_message)

    @api.constrains("cadastral_reference")
    def _check_valid_cadastral_reference(self):
        """Validate Spanish cadastral reference format"""
        for record in self:
            if record.cadastral_reference:
                try:
                    referenciacatastral.validate(record.cadastral_reference)
                except Exception as e:
                    error_message = _("Invalid Cadastral Reference: {error}").format(
                        error=e
                    )
                    raise ValidationError(error_message)

    # CRUD methods
    def _create_default_participations(self):
        """Create default participation options for the project"""
        participation_model = self.env["energy_selfconsumptions.participation"]
        for participation_data in SELFCONSUMPTION_DEFAULT_PARTICIPATIONS:
            participation_model.create(
                {
                    **participation_data,
                    "project_id": self.id,
                }
            )

    @api.model_create_multi
    def create(self, values):
        """
        Create new self-consumption project records with default participations

        Args:
            values (list): List of dictionaries containing field values

        Returns:
            recordset: Created records
        """
        res = super().create(values)
        # Create default participation options for each new project
        for record in res:
            record._create_default_participations()
        return res

    def unlink(self):
        """
        Delete self-consumption project records

        Note: Contains TODO items for additional validation logic
        """
        for record in self:
            # TODO: Add extra control when deleting supply_point_assignation_ids
            # depending on the state of the distribution_table_ids model.
            # record.distribution_table_ids.supply_point_assignation_ids.unlink()

            # TODO: Add extra control when deleting distribution_table_ids
            # depending on the status
            # record.distribution_table_ids.unlink()

            # TODO: Add extra control when deleting inscription_ids depending
            # on whether the supply_point_assignation_ids model of
            # distribution_table_ids is present. And depending on whether it is an open
            # enrollment for the public.
            # record.inscription_ids.unlink()

            record.project_id.unlink()
        return super().unlink()

    # State management methods
    def set_inscription(self):
        """Set project state to inscription"""
        for record in self:
            record.unactivate_form()
            record.write({"state": "inscription"})

    def set_inscription_activation(self):
        """Set project to inscription state and validate distribution table"""
        self.set_inscription()
        self.distribution_table_state(
            DISTRIBUTION_STATE_PROCESS, DISTRIBUTION_STATE_VALIDATED
        )

    def set_draft(self):
        """Set project state to draft"""
        for record in self:
            record.write({"state": PROJECT_STATE_DRAFT})

    def set_invoicing_mode(self):
        """Open wizard to define invoicing mode"""
        return {
            "name": _("Define Invoicing Mode"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "energy_selfconsumption.define_invoicing_mode.wizard",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
            "context": {"default_selfconsumption_id": self.id},
        }

    def action_set_new_distribution_table(self):
        """Open wizard to choose the distribution table change date."""
        self.ensure_one()
        return {
            "name": _("Set New Distribution Table"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "energy_selfconsumption.set_new_distribution_table.wizard",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
            "context": {"default_selfconsumption_id": self.id},
        }

    def set_new_distribution_table(
        self, execution_date=None, period_recurring_next_date=None
    ):
        distribution_table_active = self.distribution_table_ids.filtered(
            lambda table: table.state == DISTRIBUTION_STATE_ACTIVE
        )
        if not distribution_table_active:
            raise ValidationError(_("There is no active distribution table."))
        distribution_table_validated = self.distribution_table_ids.filtered(
            lambda table: table.state == DISTRIBUTION_STATE_VALIDATED
        )
        if not distribution_table_validated:
            raise ValidationError(_("There is no validated distribution table."))

        if not execution_date:
            execution_date = fields.Date.today()
        # Snapshot the project invoicing calendar before contracts are recreated.
        # execution_date only starts the new table; new CUPS must join this period.
        reference_contract = self.get_active_contracts()[:1]
        if not period_recurring_next_date:
            period_recurring_next_date = (
                reference_contract.recurring_next_date if reference_contract else False
            )
        reference_last_date_invoiced = (
            reference_contract.last_date_invoiced if reference_contract else False
        )

        closed_without_inscription = self.distribution_table_state(
            DISTRIBUTION_STATE_VALIDATED,
            DISTRIBUTION_STATE_ACTIVE,
            execution_date=execution_date,
            period_recurring_next_date=period_recurring_next_date,
        )

        # TODO:
        # Generate new sale orders
        # Select product
        pack = None
        if self.invoicing_mode == "power_acquired":
            pack = self.env.ref(
                "energy_selfconsumption.product_product_power_acquired_product_pack_template"
            )
        elif self.invoicing_mode == "energy_delivered":
            pack = self.env.ref(
                "energy_selfconsumption.product_product_energy_delivered_product_pack_template"
            )
        elif self.invoicing_mode == "energy_custom":
            pack = self.env.ref(
                "energy_selfconsumption.product_product_energy_custom_product_pack_template"
            )
        else:
            raise ValidationError(_("Invalid invoicing mode"))

        # Create sale order
        for (
            supply_point_assignation
        ) in distribution_table_validated.supply_point_assignation_ids:
            inscription = self._get_inscription_for_assignation(
                supply_point_assignation
            )
            supply_point = supply_point_assignation.supply_point_id
            mandate_id = self._get_inscription_mandate_id(inscription, supply_point)

            service_invoicing_id = False
            existing_contract = self._get_existing_pack_contract_for_supply_point(
                inscription.partner_id,
                supply_point,
                ["closed_planned", "in_progress", "paused", "closed"],
            )
            if not existing_contract:
                so_metadata = {
                    "selfconsumption_id": self.id,
                    "supply_point_id": supply_point.id,
                    "supply_point_assignation_id": supply_point_assignation.id,
                    "recurring_interval": self.recurring_interval,
                    "recurring_rule_type": self.recurring_rule_type,
                    "recurring_invoicing_type": self.recurring_invoicing_type,
                    "project_id": self.id,
                    "company_id": self.company_id.id,
                    "mandate_id": mandate_id,
                }
                if period_recurring_next_date:
                    so_metadata["recurring_next_date"] = period_recurring_next_date

                # create service invoicing
                with sale_order_utils(self.env) as component:
                    service_invoicing_id = component.create_service_invoicing_initial(
                        inscription.partner_id,
                        pack,
                        self.pricelist_id,
                        execution_date,
                        "activate",
                        "active_selfconsumption_contract",
                        self.payment_mode_id,
                        so_metadata,
                    )
            if not service_invoicing_id:
                existing_closed_contract = (
                    self._get_existing_pack_contract_for_supply_point(
                        inscription.partner_id,
                        supply_point,
                        ["closed_planned", "closed"],
                    )
                )
                if existing_closed_contract:
                    with contract_utils(
                        self.env, existing_closed_contract
                    ) as component:
                        service_invoicing_id = component.reopen(
                            # component.work.record.last_date_invoiced+ relativedelta(days=+1),
                            execution_date,
                            component.work.record.pricelist_id,
                            pack,
                            False,
                            component.work.record.payment_mode_id,
                        )
            if service_invoicing_id:
                # 2.- setup contract line main_line
                service_invoicing_id.contract_line_ids[0].write({"main_line": True})
                # 3.- mark contract as active
                self._drop_incompatible_last_date_invoiced(
                    service_invoicing_id, execution_date
                )
                with contract_utils(self.env, service_invoicing_id) as component:
                    component.activate(execution_date)
                self._activate_replacement_alta_contract(
                    service_invoicing_id,
                    supply_point_assignation,
                    execution_date=execution_date,
                    period_recurring_next_date=period_recurring_next_date,
                    reference_last_date_invoiced=reference_last_date_invoiced,
                )

        return closed_without_inscription

    def _get_inscription_for_assignation(self, supply_point_assignation):
        """Return the inscription of this CUPS, never every inscription of the partner."""
        self.ensure_one()
        inscription = supply_point_assignation.get_inscription()
        if not inscription:
            cups_code = (
                supply_point_assignation.supply_point_id.code
                or supply_point_assignation.supply_point_id.display_name
            )
            raise ValidationError(
                _("Inscription not found for CUPS {cups}").format(cups=cups_code)
            )
        return inscription

    def _get_inscription_mandate_id(self, inscription, supply_point, required=True):
        """Use the mandate of this CUPS inscription. Do not merge partner mandates."""
        cups_code = supply_point.code or supply_point.display_name
        if (
            inscription
            and len(inscription) > 1
            and "supply_point_id" in inscription._fields
        ):
            inscription = inscription.filtered(
                lambda rec: rec.supply_point_id.id == supply_point.id
            )
        partner_name = inscription.partner_id.name if inscription else ""
        if not inscription.mandate_id:
            if not required:
                return None
            raise ValidationError(
                _("Mandate not found for CUPS {cups} ({partner})").format(
                    cups=cups_code, partner=partner_name
                )
            )
        return inscription.mandate_id.id

    def _get_existing_pack_contract_for_supply_point(
        self, partner, supply_point, statuses
    ):
        """Find a project pack contract for this CUPS, not any CUPS of the partner."""
        self.ensure_one()
        if not partner or not supply_point:
            return self.env["contract.contract"]
        return get_existing_pack_contract(
            self.env,
            partner,
            "selfconsumption_pack",
            statuses,
            [
                ("project_id", "=", self.id),
                (
                    "supply_point_assignation_id.supply_point_id",
                    "=",
                    supply_point.id,
                ),
            ],
        )

    def set_in_activation_state(self):
        for record in self:
            if not record.code:
                raise ValidationError(_("Project must have a valid Code."))
            if not record.power or record.power <= 0:
                raise ValidationError(_("Project must have a valid Rated Power."))
            if not record.distribution_table_ids.filtered_domain(
                [("state", "=", DISTRIBUTION_STATE_VALIDATED)]
            ):
                raise ValidationError(_("Must have a valid Distribution Table."))
            record.write({"state": "activation"})
        self.distribution_table_state(
            DISTRIBUTION_STATE_VALIDATED, DISTRIBUTION_STATE_PROCESS
        )

    def activate(self):
        """
        Activates the energy self-consumption project, performing various validations.

        This method checks for the presence of a valid code, and rated power
        for the project. If all validations pass, it instances a wizard and generating
        contracts for the project.

        Note:
            The change of state for the 'self-consumption' and 'distribution_table'
            models is performed in the wizard that gets opened. These state changes
            are executed only after the contracts have been successfully generated.

        Returns:
            dict: A dictionary containing the action details for opening the wizard.

        Raises:
            ValidationError: If the project does not have a valid Code, or Rated Power.
        """
        for record in self:
            if not record.code:
                raise ValidationError(_("Project must have a valid Code."))
            if not record.power or record.power <= 0:
                raise ValidationError(_("Project must have a valid Rated Power."))
            if not record.invoicing_mode:
                raise ValidationError(
                    _("Project must have defined a invoicing mode before activation.")
                )
            return {
                "name": _("Generate Contracts"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "energy_selfconsumption.contract_generation.wizard",
                "views": [(False, "form")],
                "view_id": False,
                "target": "new",
                "context": {
                    "default_selfconsumption_id": self.id,
                    "default_company_id": self.env.company.id,
                },
            }

    def activate_form(self):
        self.ensure_one()  # Ensures only one record is selected
        if self.conf_state != SELFCONSUMPTION_CONF_STATE_ACTIVE:
            if not self.company_id.data_policy_approval_text:
                raise ValidationError(
                    _(
                        "You need to add the privacy policy file to display the form."
                        "To modify the privacy policy go to company settings."
                    )
                )
            self.conf_state = SELFCONSUMPTION_CONF_STATE_ACTIVE
            self.conf_url_form = (
                "{base_url}/inscription-data?model_id={model_id}".format(
                    base_url=self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("web.base.url"),
                    model_id=self._origin.id,
                )
            )

    def unactivate_form(self):
        self.ensure_one()  # Ensures only one record is selected
        if self.conf_state == SELFCONSUMPTION_CONF_STATE_ACTIVE:
            self.conf_url_form = ""
            self.conf_state = SELFCONSUMPTION_CONF_STATE_INACTIVE

    def action_redirect_to_page_form_inscription(self):
        self.ensure_one()  # Ensures only one record is selected
        return {
            "type": "ir.actions.act_url",
            "url": self.conf_url_form,
            "target": "new",
        }

    def get_distribution_tables_view(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Distribution Tables",
            "view_mode": "tree,form",
            "res_model": "energy_selfconsumption.distribution_table",
            "domain": [("selfconsumption_project_id", "=", self.id)],
            "context": {"create": True, "default_selfconsumption_project_id": self.id},
        }

    def get_inscriptions_view(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Inscriptions",
            "view_mode": "tree,form",
            "res_model": "energy_selfconsumption.inscription_selfconsumption",
            "domain": [
                ("project_id", "=", self.project_id.id),
                ("selfconsumption_project_id", "=", self.id),
            ],
            "context": {
                "create": True,
                "default_project_id": self.project_id.id,
                "default_selfconsumption_project_id": self.id,
            },
        }

    def get_sale_orders(self):
        return (
            self.env["sale.order.metadata.line"]
            .search([("key", "=", "selfconsumption_id"), ("value", "=", str(self.id))])
            .mapped("order_id")
        )

    def get_sale_orders_view(self):
        self.ensure_one()
        sale_orders = self.get_sale_orders()
        return {
            "type": "ir.actions.act_window",
            "name": "Sale Orders",
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "domain": [("id", "in", sale_orders.ids)],
        }

    # TODO: Review if we need to use all contracts or only the active ones when this method is used
    def get_contracts(self):
        return self.env["contract.contract"].search([("project_id", "=", self.id)])

    def get_active_contracts(self):
        return self.env["contract.contract"].search(
            [("project_id", "=", self.id), ("status", "=", "in_progress")]
        )

    def get_contracts_view(self):
        self.ensure_one()
        contracts = self.get_contracts()
        return {
            "type": "ir.actions.act_window",
            "name": "Contracts",
            "view_type": "tree",
            "view_mode": "tree,form",
            "views": [
                (
                    self.env.ref(
                        "energy_communities_service_invoicing.view_service_invoicing_tree"
                    ).id,
                    "tree",
                ),
                (
                    self.env.ref(
                        "energy_communities_service_invoicing.view_contract_contract_customer_form_platform_admin"
                    ).id,
                    "form",
                ),
            ],
            "res_model": "contract.contract",
            "domain": [("id", "in", contracts.ids)],
            "context": {
                "create": True,
                "default_project_id": self.id,
                "search_default_not_finished": 1,
                "search_default_paused": 1,
            },
            "target": "current",
        }

    def check_dates_contract(self, contracts=None):
        if contracts is None:
            contracts = self.get_active_contracts()
        if not contracts:
            return True
        last_date_invoiced = contracts[0].last_date_invoiced
        if contracts.filtered(
            lambda contract: contract.last_date_invoiced != last_date_invoiced
        ):
            raise ValidationError(
                self._format_inconsistent_contract_dates_message(
                    "The last date invoiced is not the same for all contracts.",
                    contracts,
                    "last_date_invoiced",
                )
            )
        next_period_date_start = contracts[0].next_period_date_start
        if contracts.filtered(
            lambda contract: contract.next_period_date_start != next_period_date_start
        ):
            raise ValidationError(
                _("The next period date start is not the same for all contracts.")
            )
        next_period_date_end = contracts[0].next_period_date_end
        if contracts.filtered(
            lambda contract: contract.next_period_date_end != next_period_date_end
        ):
            raise ValidationError(
                _("The next period date end is not the same for all contracts.")
            )
        recurring_next_date = contracts[0].recurring_next_date
        if contracts.filtered(
            lambda contract: contract.recurring_next_date != recurring_next_date
        ):
            raise ValidationError(
                _("The recurring next date is not the same for all contracts.")
            )

        recurring_invoicing_type = contracts[0].recurring_invoicing_type
        if contracts.filtered(
            lambda contract: contract.recurring_invoicing_type
            != recurring_invoicing_type
        ):
            raise ValidationError(
                _("The recurring invoicing type is not the same for all contracts.")
            )
        if last_date_invoiced and recurring_invoicing_type in (
            RECURRING_INVOICING_TYPE_POSTPAID,
            RECURRING_INVOICING_TYPE_PREPAID,
        ):
            mismatched = contracts.filtered(
                lambda contract: contract.recurring_next_date
                != self._expected_recurring_next_date(contract)
            )
            if mismatched:
                raise ValidationError(
                    self._format_inconsistent_contract_dates_message(
                        "The recurring next date is not consistent with the next "
                        "invoicing period and invoicing offset for all contracts.",
                        mismatched,
                        "recurring_next_date",
                    )
                )
        return True

    def _expected_recurring_next_date(self, contract):
        """Invoice date implied by period bounds and recurring_invoicing_offset."""
        offset = contract.recurring_invoicing_offset or 0
        if contract.recurring_invoicing_type == RECURRING_INVOICING_TYPE_POSTPAID:
            period_ref = contract.next_period_date_end
        elif contract.recurring_invoicing_type == RECURRING_INVOICING_TYPE_PREPAID:
            period_ref = contract.next_period_date_start
        else:
            return False
        if not period_ref:
            return False
        return period_ref + relativedelta(days=offset)

    def _format_inconsistent_contract_dates_message(
        self, message, contracts, field_name
    ):
        """Build a validation message that lists each contract date value."""
        details = [
            "%s (id=%s): %s=%s"
            % (
                contract.display_name,
                contract.id,
                field_name,
                getattr(contract, field_name) or False,
            )
            for contract in contracts
        ]
        return "{}\n{}".format(_(message), "\n".join(details))

    def distribution_table_state(
        self,
        actual_state,
        new_state,
        execution_date=None,
        period_recurring_next_date=None,
    ):
        self.check_dates_contract()
        if not execution_date:
            execution_date = fields.Date.today()
        table_end_date = execution_date - relativedelta(days=1)
        distribution_table_to_activate = self.distribution_table_ids.filtered(
            lambda table: table.state == actual_state
        )
        distribution_table_active = self.distribution_table_ids.filtered(
            lambda table: table.state == DISTRIBUTION_STATE_ACTIVE
        )
        # If the new state is active, we need to cancel the active distribution table
        if new_state == DISTRIBUTION_STATE_ACTIVE and distribution_table_active:
            distribution_table_active.write(
                {"date_end": table_end_date, "state": DISTRIBUTION_STATE_CANCELLED}
            )
        distribution_table_to_activate.write({"state": new_state})
        if new_state == DISTRIBUTION_STATE_ACTIVE:
            # We need to update the start date of the distribution table
            distribution_table_to_activate.write({"date_start": execution_date})
            # If the new state is active, we need to update the inscriptions
            for supply_point_assignation in distribution_table_to_activate.mapped(
                "supply_point_assignation_ids"
            ):
                inscription = self._get_inscription_for_assignation(
                    supply_point_assignation
                )
                inscription.write(
                    {
                        "participation_real_quantity": supply_point_assignation.energy_shares,
                        "state": INSCRIPTION_STATE_ACTIVE,
                    }
                )
                supply_point_assignation_ids = distribution_table_active.mapped(
                    "supply_point_assignation_ids"
                ).filtered(
                    lambda assignation: assignation.supply_point_id.id
                    == inscription.supply_point_id.id
                )
                for supply_point_assignation_id in supply_point_assignation_ids:
                    contract = supply_point_assignation_id.get_contract()
                    if not contract:
                        continue
                    # Capture dates before modify(): close() sets date_end and
                    # can clear next-period fields on the predecessor.
                    predecessor_last_date_invoiced = contract.last_date_invoiced
                    predecessor_recurring_next_date = contract.recurring_next_date
                    modify_date = (
                        predecessor_last_date_invoiced
                        or execution_date - relativedelta(days=1)
                    )
                    activate_date = execution_date
                    # The stub last date belongs to the closed predecessor. OCA
                    # forbids putting it on a successor whose date_start is later.
                    successor_last_date_invoiced = (
                        self._last_date_invoiced_for_new_contract(
                            predecessor_last_date_invoiced, activate_date
                        )
                    )
                    modify_metadata = {
                        "selfconsumption_id": self.id,
                        "supply_point_id": supply_point_assignation.supply_point_id.id,
                        "supply_point_assignation_id": supply_point_assignation.id,
                        "recurring_interval": self.recurring_interval,
                        "recurring_rule_type": self.recurring_rule_type,
                        "recurring_invoicing_type": self.recurring_invoicing_type,
                        "project_id": self.id,
                        "company_id": self.company_id.id,
                        "mandate_id": self._get_inscription_mandate_id(
                            inscription,
                            supply_point_assignation.supply_point_id,
                            required=False,
                        ),
                    }
                    if successor_last_date_invoiced:
                        modify_metadata[
                            "last_date_invoiced"
                        ] = successor_last_date_invoiced
                    if predecessor_recurring_next_date:
                        modify_metadata[
                            "recurring_next_date"
                        ] = predecessor_recurring_next_date
                    elif period_recurring_next_date:
                        modify_metadata[
                            "recurring_next_date"
                        ] = period_recurring_next_date
                    with contract_utils(self.env, contract) as component:
                        new_contract = component.modify(
                            execution_date=modify_date,
                            executed_modification_action="modify",
                            pricelist_id=contract.pricelist_id,
                            pack_id=contract.pack_id,
                            discount=contract.discount,
                            payment_mode_id=contract.payment_mode_id,
                            metadata=modify_metadata,
                        )
                    with contract_utils(self.env, new_contract) as component:
                        # 2.- setup contract line main_line
                        component.work.record.contract_line_ids[0].write(
                            {"main_line": True}
                        )
                        # 3.- mark contract as active
                        self._drop_incompatible_last_date_invoiced(
                            new_contract, activate_date
                        )
                        component.activate(activate_date)
                    self._align_new_contract_period_end(
                        new_contract,
                        period_recurring_next_date,
                        last_date_invoiced=successor_last_date_invoiced,
                        recurring_next_date=predecessor_recurring_next_date
                        or period_recurring_next_date,
                    )
            inscriptions = self.inscription_ids.filtered_domain(
                [("state", "=", INSCRIPTION_STATE_CHANGE)]
            )
            inscriptions.write({"state": "cancelled"})
            for inscription in inscriptions:
                supply_point_assignation_id = distribution_table_active.mapped(
                    "supply_point_assignation_ids"
                ).filtered(
                    lambda assignation: assignation.supply_point_id.id
                    == inscription.supply_point_id.id
                )
                contract = supply_point_assignation_id.get_contract()
                if contract:
                    self._leave_contract_on_replacement(
                        contract,
                        supply_point_assignation_id,
                        execution_date,
                    )
            closed_without_inscription = (
                self._close_outgoing_contracts_not_in_new_table(
                    distribution_table_active, distribution_table_to_activate
                )
            )
            if closed_without_inscription:
                self._notify_contracts_closed_without_inscription(
                    closed_without_inscription
                )
            self.check_dates_contract()
            return closed_without_inscription
        return self.env["contract.contract"]

    def _close_outgoing_contracts_not_in_new_table(
        self, outgoing_table, incoming_table
    ):
        """Close leftover in-progress contracts of CUPS that left the table.

        Inscriptions in change state are closed above. CUPS whose inscription
        was removed instead of marked as change still keep an open contract on
        the outgoing table; those must be closed as well so date checks only
        see the new table contracts.
        """
        closed_contracts = self.env["contract.contract"]
        incoming_supply_points = incoming_table.mapped(
            "supply_point_assignation_ids.supply_point_id"
        )
        for assignation in outgoing_table.mapped("supply_point_assignation_ids"):
            if assignation.supply_point_id in incoming_supply_points:
                continue
            contract = assignation.get_contract()
            if contract and contract.status == "in_progress":
                leave_date = incoming_table.date_start
                if not leave_date:
                    continue
                self._leave_contract_on_replacement(contract, assignation, leave_date)
                closed_contracts |= contract
        return closed_contracts

    def _notify_contracts_closed_without_inscription(self, contracts):
        """Record leftover closures on the project chatter."""
        self.ensure_one()
        if not contracts:
            return
        details = "\n".join(
            self._format_closed_contract_without_inscription(contract)
            for contract in contracts
        )
        self.message_post(
            body=_(
                "The following %(count)s contract(s) were closed because their "
                "CUPS are not included in the new distribution table and had no "
                "inscription in change state:\n%(details)s"
            )
            % {"count": len(contracts), "details": details}
        )

    def _format_closed_contract_without_inscription(self, contract):
        cups_code = contract.supply_point_assignation_id.supply_point_id.code or _(
            "Unknown CUPS"
        )
        return "- {} ({}, id={})".format(cups_code, contract.display_name, contract.id)

    def _prepaid_alta_stub_dates(self, execution_date, current_period_end):
        """Invoice the new CUPS from the replacement date to the current period end."""
        if (
            not execution_date
            or not current_period_end
            or execution_date > current_period_end
        ):
            return False, False
        return execution_date, current_period_end

    def _prepaid_baja_stub_dates(
        self, last_date_invoiced, execution_date, fallback_start=None
    ):
        """Invoice a leaving CUPS from the day after last invoice until the day before leave."""
        stub_end = execution_date - relativedelta(days=1) if execution_date else False
        stub_start = (
            last_date_invoiced + relativedelta(days=1)
            if last_date_invoiced
            else fallback_start
        )
        if not stub_start or not stub_end or stub_start > stub_end:
            return False, False
        return stub_start, stub_end

    def _clip_contract_next_invoice_period(self, contract, period_start, period_end):
        """Force the next invoice to cover only [period_start, period_end]."""
        lines = contract.contract_line_ids.filtered(lambda line: not line.is_canceled)
        if not lines or not period_start or not period_end:
            return
        date_start = lines[0].date_start or contract.date_start
        last_date = period_start - relativedelta(days=1)
        offset = contract.recurring_invoicing_offset or 0
        if contract.recurring_invoicing_type == RECURRING_INVOICING_TYPE_PREPAID:
            pff = period_start + relativedelta(days=offset)
        else:
            pff = period_end + relativedelta(days=offset)
        vals = {"recurring_next_date": pff}
        # OCA forbids date_start > last_date_invoiced. A new CUPS starting on
        # period_start must keep last empty so the stub starts at date_start.
        if not (date_start and last_date and date_start > last_date):
            vals["last_date_invoiced"] = last_date
        # OCA forbids date_end < last_date_invoiced.
        effective_last = vals.get("last_date_invoiced") or lines[0].last_date_invoiced
        if not effective_last or period_end >= effective_last:
            vals["date_end"] = period_end
        lines.write(vals)
        lines._compute_next_period_date_start()
        lines._compute_next_period_date_end()
        lines._compute_recurring_next_date()
        with contract_utils(self.env, contract) as component:
            component.propagate_recurrency_values_to_contract()

    def _invoice_power_acquired_stub(
        self, contract, assignation, period_start, period_end
    ):
        """Create the power-acquired stub invoice and set quantity from days in period."""
        if not contract or not assignation or not period_start or not period_end:
            return self.env["account.move"]
        self._clip_contract_next_invoice_period(contract, period_start, period_end)
        invoice = contract.recurring_create_invoice()
        if not invoice:
            return self.env["account.move"]
        moves = invoice
        if getattr(invoice, "_name", None) != "account.move":
            moves = self.env["account.move"].browse(invoice)
        moves = moves.exists()
        days_invoiced = (period_end - period_start).days + 1
        qty = round(assignation.coefficient, 6) * self.power * days_invoiced
        note = _(
            "NOTE: There are only {days_invoiced} active invoiceble days to take in consideration into the current invoiced period for this supply point. {coefficient} * {power} Kw * {days_invoiced} days = {qty} KwH"
        ).format(
            days_invoiced=days_invoiced,
            coefficient=round(assignation.coefficient, 6),
            power=self.power,
            qty=qty,
        )
        for move in moves:
            product_lines = move.invoice_line_ids.filtered(
                lambda line: line.display_type not in ("line_section", "line_note")
            )
            if not product_lines:
                continue
            product_lines[0].write({"quantity": qty, "sequence": 2})
            move.write(
                {
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "display_type": "line_note",
                                "name": note,
                                "sequence": 1,
                            }
                        )
                    ],
                }
            )
        return moves

    def _activate_replacement_alta_contract(
        self,
        contract,
        assignation,
        execution_date=None,
        period_recurring_next_date=None,
        reference_last_date_invoiced=None,
    ):
        """Invoice the prepaid alta stub, then park every new CUPS on the project calendar.

        Prepaid power-acquired altas bill execution_date -> current period end, then
        last_date_invoiced/PFF match continuing CUPS. Postpaid altas only join the
        remaining period; they are not invoiced here.
        """
        if not contract:
            return
        is_alta = (
            not contract.predecessor_contract_id and not contract.successor_contract_id
        )
        stub_start, stub_end = self._prepaid_alta_stub_dates(
            execution_date, reference_last_date_invoiced
        )
        if (
            is_alta
            and self.invoicing_mode == SELFCONSUMPTION_INVOICING_MODE_POWER_ACQUIRED
            and self.recurring_invoicing_type == RECURRING_INVOICING_TYPE_PREPAID
            and stub_start
            and stub_end
        ):
            self._invoice_power_acquired_stub(
                contract, assignation, stub_start, stub_end
            )
            next_pff = stub_end + relativedelta(days=1)
            self._align_new_contract_period_end(
                contract,
                next_pff,
                last_date_invoiced=stub_end,
                recurring_next_date=next_pff,
            )
            return
        self._align_new_contract_period_end(
            contract,
            period_recurring_next_date,
            last_date_invoiced=self._last_date_invoiced_for_new_contract(
                reference_last_date_invoiced,
                execution_date or contract.date_start,
            ),
            recurring_next_date=period_recurring_next_date,
        )

    def _close_date_for_replacement(self, contract, proposed_end):
        """Never end a line before last_date_invoiced (OCA contract constraint)."""
        last = contract.last_date_invoiced if contract else False
        if last and (not proposed_end or proposed_end < last):
            return last
        return proposed_end

    def _leave_contract_on_replacement(self, contract, assignation, execution_date):
        """Invoice the unbilled prepaid stub of a leaving CUPS, then close it."""
        if not contract or not execution_date:
            return
        close_date = execution_date - relativedelta(days=1)
        stub_start, stub_end = self._prepaid_baja_stub_dates(
            contract.last_date_invoiced,
            execution_date,
            fallback_start=contract.next_period_date_start or contract.date_start,
        )
        if (
            self.invoicing_mode == SELFCONSUMPTION_INVOICING_MODE_POWER_ACQUIRED
            and self.recurring_invoicing_type == RECURRING_INVOICING_TYPE_PREPAID
            and assignation
            and stub_start
            and stub_end
        ):
            self._invoice_power_acquired_stub(
                contract, assignation, stub_start, stub_end
            )
            close_date = stub_end
        close_date = self._close_date_for_replacement(contract, close_date)
        with contract_utils(self.env, contract) as component:
            component.close(close_date or contract.last_date_invoiced)

    def _last_date_invoiced_for_new_contract(self, last_date_invoiced, date_start):
        """Keep last_date_invoiced only when it does not precede the new line start.

        OCA contract.line forbids date_start > last_date_invoiced. After a
        post-paid stub the predecessor last date is the day before the
        replacement; that date belongs to the closed contract, not the successor.
        """
        if not last_date_invoiced:
            return False
        if date_start and date_start > last_date_invoiced:
            return False
        return last_date_invoiced

    def _drop_incompatible_last_date_invoiced(self, contract, date_start):
        """Clear last_date_invoiced before moving date_start past it."""
        if not contract or not date_start:
            return
        lines = contract.contract_line_ids.filtered(
            lambda line: not line.is_canceled
            and line.last_date_invoiced
            and date_start > line.last_date_invoiced
        )
        if lines:
            lines.write({"last_date_invoiced": False})

    def _align_new_contract_period_end(
        self,
        new_contract,
        period_recurring_next_date,
        last_date_invoiced=None,
        recurring_next_date=None,
    ):
        """Restore invoicing dates after contract.utils recreates recurrency.

        Continuing CUPS keep the predecessor last invoiced date and PFF/PPC/PPF
        when that last date is still valid on the new line. New CUPS join the
        same project calendar; execution_date is not a new invoicing period start.
        """
        if not new_contract:
            return
        last_date_invoiced = self._last_date_invoiced_for_new_contract(
            last_date_invoiced,
            new_contract.date_start or new_contract.contract_line_ids[:1].date_start,
        )
        if last_date_invoiced or recurring_next_date:
            self._write_invoicing_dates_on_contract(
                new_contract,
                last_date_invoiced=last_date_invoiced,
                recurring_next_date=recurring_next_date,
            )
            return
        if period_recurring_next_date:
            self._write_invoicing_dates_on_contract(
                new_contract, recurring_next_date=period_recurring_next_date
            )

    def _write_invoicing_dates_on_contract(
        self, contract, last_date_invoiced=None, recurring_next_date=None
    ):
        lines = contract.contract_line_ids.filtered(lambda line: not line.is_canceled)
        if not lines:
            return
        last_date_invoiced = self._last_date_invoiced_for_new_contract(
            last_date_invoiced, lines[0].date_start or contract.date_start
        )
        # Stub invoicing clips date_end so the next invoice can end mid-period.
        # After that invoice, the contract must stay open for the remaining
        # calendar; otherwise the next period is capped at the stub end.
        vals = {}
        if any(lines.mapped("date_end")):
            vals["date_end"] = False
        if last_date_invoiced:
            vals["last_date_invoiced"] = last_date_invoiced
        if vals:
            lines.write(vals)
            lines._compute_next_period_date_start()
        if recurring_next_date:
            # Write after period-start compute so recurrency does not rebuild
            # the invoice date from date_start / interval.
            lines.write({"recurring_next_date": recurring_next_date})
            lines._compute_next_period_date_end()
        with contract_utils(self.env, contract) as component:
            component.propagate_recurrency_values_to_contract()

    def get_table_change_in_period(self, period_start, period_end):
        """Return active and cancelled tables if a replacement happened in the period."""
        self.ensure_one()
        empty = self.env["energy_selfconsumption.distribution_table"]
        if not period_start or not period_end:
            return empty, empty
        active_tables = self.distribution_table_ids.filtered(
            lambda table: table.state == DISTRIBUTION_STATE_ACTIVE
            and table.date_start
            and period_start <= table.date_start <= period_end
        )
        cancelled_tables = self.distribution_table_ids.filtered(
            lambda table: table.state == DISTRIBUTION_STATE_CANCELLED
            and table.date_end
            and period_start <= table.date_end <= period_end
        )
        if active_tables and cancelled_tables:
            return active_tables[:1], cancelled_tables[:1]
        return empty, empty

    def validate_state(self, state):
        if state not in (PROJECT_STATE_ACTIVATION, PROJECT_STATE_ACTIVE):
            error_message = _(
                "The report can be downloaded when the project is in activation or active status."
            )
            raise ValidationError(error_message)

    def action_export_csv_inscriptions_wizard(self):
        self.ensure_one()
        wizard = (
            self.env["export.csv.inscritions.wizard"]
            .with_context(
                {
                    "active_id": self.id,
                }
            )
            .create({})
        )
        return wizard.exportar_csv()

    def _set_report_distribution_table(self):
        """
        Get the distribution table needed to generate reports.
        Prioritizes tables in process state, then active ones.
        Only one table of each type should exist.
        """
        for record in self:
            if self.env.context.get("distribution_table_id", False):
                record.report_distribution_table = (
                    record.distribution_table_ids.filtered_domain(
                        [("id", "=", self.env.context.get("distribution_table_id"))]
                    )
                )
            else:
                table_in_process = record.distribution_table_ids.filtered_domain(
                    [("state", "=", DISTRIBUTION_STATE_PROCESS)]
                )
                table_in_active = record.distribution_table_ids.filtered_domain(
                    [("state", "=", DISTRIBUTION_STATE_ACTIVE)]
                )
                if table_in_process:
                    record.report_distribution_table = table_in_process
                elif table_in_active:
                    record.report_distribution_table = table_in_active
                else:
                    raise ValidationError(_("No distribution table found"))

    def action_manager_authorization_report(self):
        self.ensure_one()
        self._set_report_distribution_table()
        self.validate_state(self.state)
        return self.env.ref(
            "energy_selfconsumption.selfconsumption_manager_authorization_report"
        ).report_action(self)

    def action_power_sharing_agreement_report(self):
        self.ensure_one()
        self._set_report_distribution_table()
        self.validate_state(self.state)
        return self.env.ref(
            "energy_selfconsumption.power_sharing_agreement_report"
        ).report_action(self)

    def action_manager_partition_coefficient_report(self):
        self.ensure_one()
        self._set_report_distribution_table()
        self.validate_state(self.state)
        tables_to_use = self.report_distribution_table
        file_content = StringIO()
        if tables_to_use.type == "fixed":
            for table in tables_to_use:
                for index, assignation in enumerate(table.supply_point_assignation_ids):
                    coefficient_format = f"{assignation.coefficient:.6f}"
                    if index == len(table.supply_point_assignation_ids) - 1:
                        file_content.write(
                            f"{assignation.supply_point_id.code};{coefficient_format.replace('.', ',')}"
                        )
                    else:
                        file_content.write(
                            f"{assignation.supply_point_id.code};{coefficient_format.replace('.', ',')}\r\n"
                        )
        else:
            file_data = base64.b64decode(
                tables_to_use.hourly_coefficients_imported_file
            )
            self.ensure_one()
            try:
                try:
                    decoded_file = file_data.decode(
                        tables_to_use.hourly_coefficients_imported_encoding
                    )
                except UnicodeDecodeError:
                    detected_encoding = chardet.detect(file_data).get("encoding", False)
                    if not detected_encoding:
                        raise ValidationError(
                            _("No valid encoding was found for the attached file")
                        )
                    decoded_file = file_data.decode(detected_encoding)

                df = pd.read_csv(
                    StringIO(decoded_file),
                    delimiter=tables_to_use.hourly_coefficients_imported_delimiter,
                    quotechar=tables_to_use.hourly_coefficients_imported_quotechar,
                )
                try:
                    for index, row in df.iterrows():
                        hour = int(row["hour"])
                        hour_str = str(hour).zfill(4)
                        for index, column in enumerate(df.columns[1:]):
                            coefficient_format = f"{row[column]:.6f}"
                            if index == len(df.columns[1:]) - 1:
                                file_content.write(
                                    f"{column};{hour_str};{coefficient_format.replace('.', ',')}"
                                )
                            else:
                                file_content.write(
                                    f"{column};{hour_str};{coefficient_format.replace('.', ',')}\r\n"
                                )
                except Exception:
                    raise ValidationError(_("Error reading file"))
            except Exception:
                raise ValidationError(_("Error parsing the file"))

        date = datetime.now()
        year = date.strftime("%Y")
        report = self.env["energy_selfconsumption.coefficient_report"].create(
            {
                "report_data": file_content.getvalue(),
                "file_name": f"{self.code}_{year}.txt",
            }
        )
        file_content.close()
        url = "/energy_selfconsumption/download_report?id=%s" % report.id
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
        }

    def send_energy_delivery_invoicing_reminder(self):
        today = fields.date.today()
        date_validation = today + timedelta(days=3)

        projects = self.env["contract.contract"].read_group(
            [
                (
                    "project_id.selfconsumption_id.invoicing_mode",
                    "=",
                    "energy_delivered",
                ),
                ("recurring_next_date", "=", date_validation),
            ],
            ["project_id"],
            ["project_id"],
        )
        template = self.env.ref(
            "energy_selfconsumption.selfconsumption_energy_delivered_invoicing_reminder",
            True,
        )
        for project in projects:
            # project["project_id"][0] - project.project_id.id
            selfconsumption_id = self.browse(project["project_id"][0])
            contract = selfconsumption_id.contract_ids[0]
            first_date = contract.next_period_date_start
            last_date = contract.next_period_date_end
            next_invoicing = contract.recurring_next_date
            ctx = {
                "next_invoicing": next_invoicing.strftime("%d-%m-%Y"),
                "first_date": first_date.strftime("%d-%m-%Y"),
                "last_date": last_date.strftime("%d-%m-%Y"),
            }
            template.with_context(ctx).send_mail(
                force_send=True,
                res_id=selfconsumption_id.id,
                email_layout_xmlid="mail.mail_notification_layout",
            )

    def send_energy_delivery_custom_invoicing_reminder(self):
        projects = self.env["contract.contract"].read_group(
            [
                (
                    "project_id.selfconsumption_id.invoicing_mode",
                    "=",
                    "energy_custom",
                ),
                ("recurring_next_date", "=", fields.date.today()),
            ],
            ["project_id"],
            ["project_id"],
        )
        template = self.env.ref(
            "energy_selfconsumption.selfconsumption_energy_delivered_custom_invoicing_reminder",
            True,
        )
        for project in projects:
            # project["project_id"][0] - project.project_id.id
            selfconsumption_id = self.browse(project["project_id"][0])
            contract = selfconsumption_id.contract_ids[0]
            first_date = contract.next_period_date_start
            last_date = contract.next_period_date_end
            next_invoicing = contract.recurring_next_date
            ctx = {
                "next_invoicing": next_invoicing.strftime("%d-%m-%Y"),
                "first_date": first_date.strftime("%d-%m-%Y"),
                "last_date": last_date.strftime("%d-%m-%Y"),
            }
            template.with_context(ctx).send_mail(
                force_send=True,
                res_id=selfconsumption_id.id,
                email_layout_xmlid="mail.mail_notification_layout",
            )

    def send_power_acquired_invoicing_reminder(self):
        today = fields.date.today()
        projects = self.env["contract.contract"].read_group(
            [
                (
                    "project_id.selfconsumption_id.invoicing_mode",
                    "=",
                    "power_acquired",
                ),
                ("recurring_next_date", "=", today),
            ],
            ["project_id"],
            ["project_id"],
        )
        template = self.env.ref(
            "energy_selfconsumption.selfconsumption_power_acquired_invoicing_reminder",
            True,
        )
        for project in projects:
            # project["project_id"][0] - project.project_id.id
            selfconsumption_id = self.browse(project["project_id"][0])
            contract = selfconsumption_id.contract_ids[0]
            next_invoicing = contract.recurring_next_date
            ctx = {
                "next_invoicing": next_invoicing.strftime("%d-%m-%Y"),
            }
            template.with_context(ctx).send_mail(
                force_send=True,
                res_id=selfconsumption_id.id,
                email_layout_xmlid="mail.mail_notification_layout",
            )


class CoefficientReport(models.TransientModel):
    _name = "energy_selfconsumption.coefficient_report"
    _description = "Generate Partition Coefficient Report"

    report_data = fields.Text("Report Data", readonly=True)
    file_name = fields.Char("File Name", readonly=True)
