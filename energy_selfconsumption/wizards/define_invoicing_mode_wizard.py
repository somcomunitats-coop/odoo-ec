from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities.utils import sale_order_utils
from odoo.addons.energy_communities_service_invoicing.config import (
    CONTRACT_ACTION_ACTIVATE,
    DEFAULT_PRICELIST_BASE_PRICE,
    DEFAULT_PRICELIST_COMPUTE_FIXED,
    DEFAULT_PRICELIST_DISCOUNT_POLICY,
    RECURRING_RULE_MONTHLY,
    RECURRING_RULE_MONTHLY_LAST_DAY,
    SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF,
)

from ..config import (
    DISTRIBUTION_STATE_PROCESS,
    SELFCONSUMPTION_DEFAULT_INVOICING_MODE,
    SELFCONSUMPTION_INVOICING_MODE_ENERGY_CUSTOM,
    SELFCONSUMPTION_INVOICING_MODE_VALUES,
    SELFCONSUMPTION_PRODUCT_REFS,
)


class DefineInvoicingModeWizard(models.TransientModel):
    """
    Define Invoicing Mode Wizard

    This wizard handles the configuration of invoicing mode for self-consumption
    projects, including:
    - Invoicing mode selection and validation
    - Contract template creation
    - Pricelist generation with custom pricing
    - Sale order creation for all participants
    - Distribution table integration

    Features:
    - Multiple invoicing mode support
    - Automatic recurring configuration
    - Mandate validation
    - Bulk contract generation
    - Error handling and validation
    """

    _name = "energy_selfconsumption.define_invoicing_mode.wizard"
    _description = "Service to generate contract"
    _inherit = ["contract.recurrency.mixin"]

    # Invoicing configuration fields
    invoicing_mode = fields.Selection(
        SELFCONSUMPTION_INVOICING_MODE_VALUES,
        string="Invoicing Mode",
        default=SELFCONSUMPTION_DEFAULT_INVOICING_MODE,
        required=True,
        help="Mode of invoicing for the self-consumption project",
    )
    price = fields.Float(
        required=True, help="Price per unit for the selected invoicing mode"
    )

    # Project relationship
    selfconsumption_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption",
        readonly=True,
        help="Self-consumption project to configure",
    )

    # Onchange methods
    @api.onchange("invoicing_mode")
    def _onchange_invoicing_mode(self):
        """
        Update recurring configuration based on invoicing mode

        Sets appropriate recurring rule type based on the selected
        invoicing mode to ensure proper billing cycles.
        """
        if self.invoicing_mode == SELFCONSUMPTION_INVOICING_MODE_ENERGY_CUSTOM:
            self.recurring_rule_type = RECURRING_RULE_MONTHLY
        else:
            self.recurring_rule_type = RECURRING_RULE_MONTHLY_LAST_DAY

    # Validation methods
    def _validate_wizard_data(self):
        """
        Validate wizard data before processing

        Raises:
            ValidationError: If validation fails
        """
        if not self.selfconsumption_id:
            raise ValidationError(_("No self-consumption project selected"))

        if not self.invoicing_mode:
            raise ValidationError(_("Invoicing mode is required"))

        if self.price <= 0:
            raise ValidationError(_("Price must be greater than zero"))

        if self.invoicing_mode not in dict(SELFCONSUMPTION_INVOICING_MODE_VALUES):
            raise ValidationError(_("Invalid invoicing mode selected"))

    def _validate_distribution_table(self):
        """
        Validate distribution table availability

        Returns:
            recordset: Distribution table in process state

        Raises:
            ValidationError: If no valid distribution table found
        """
        distribution_tables = self.selfconsumption_id.distribution_table_ids.filtered(
            lambda dt: dt.state == DISTRIBUTION_STATE_PROCESS
        )

        if not distribution_tables:
            raise ValidationError(
                _(
                    "No distribution table found in process state for project '{project}'"
                ).format(project=self.selfconsumption_id.name)
            )

        return distribution_tables[0]

    def _validate_mandates(self, distribution_table):
        """
        Validate that all participants have valid mandates

        Args:
            distribution_table: Distribution table record

        Raises:
            ValidationError: If any participant lacks a mandate
        """
        missing_mandates = []

        for assignation in distribution_table.supply_point_assignation_ids:
            partner = assignation.supply_point_id.partner_id
            inscription = self.selfconsumption_id.inscription_ids.filtered(
                lambda i: i.partner_id == partner
            )

            if inscription and not inscription.mandate_id:
                missing_mandates.append(partner.name or partner.display_name)

        if missing_mandates:
            raise ValidationError(
                _(
                    "The following participants are missing mandates:\n{partners}"
                ).format(partners="\n".join(f"- {name}" for name in missing_mandates))
            )

    # Product and template methods
    def _get_product_references(self):
        """
        Get product template and pack references for invoicing mode

        Returns:
            tuple: (product_template, pack_template)

        Raises:
            ValidationError: If product references not found
        """
        if self.invoicing_mode not in SELFCONSUMPTION_PRODUCT_REFS:
            raise ValidationError(
                _("No product configuration found for invoicing mode '{mode}'").format(
                    mode=self.invoicing_mode
                )
            )

        refs = SELFCONSUMPTION_PRODUCT_REFS[self.invoicing_mode]

        try:
            product_template = self.env.ref(refs["template"])
            pack_template = self.env.ref(refs["pack"])
            return product_template, pack_template
        except Exception as e:
            raise ValidationError(
                _("Error loading product templates for mode '{mode}': {error}").format(
                    mode=self.invoicing_mode, error=str(e)
                )
            )

    # Pricelist creation methods
    def _create_pricelist(self, product_template):
        """
        Create pricelist for the invoicing mode

        Args:
            product_template: Product template record

        Returns:
            product.pricelist: Created pricelist
        """
        pricelist_name = f"{self.selfconsumption_id.name} {self.invoicing_mode} Selfconsumption Pricelist"

        # Get service category
        service_category = self.env.ref(SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF)

        pricelist_data = {
            "name": pricelist_name,
            "company_id": self.selfconsumption_id.company_id.id,
            "currency_id": self.selfconsumption_id.company_id.currency_id.id,
            "discount_policy": DEFAULT_PRICELIST_DISCOUNT_POLICY,
            "item_ids": [
                (
                    0,
                    0,
                    {
                        "base": DEFAULT_PRICELIST_BASE_PRICE,
                        "product_tmpl_id": product_template.id,
                        "product_id": product_template.product_variant_id.id,
                        "compute_price": DEFAULT_PRICELIST_COMPUTE_FIXED,
                        "fixed_price": self.price,
                        "categ_id": service_category.id,
                    },
                )
            ],
        }

        return self.env["product.pricelist"].create(pricelist_data)

    # Sale order creation methods
    def _create_sale_orders(self, distribution_table, pack_template, pricelist):
        """
        Create sale orders for all participants

        Args:
            distribution_table: Distribution table record
            pack_template: Pack template record
            pricelist: Pricelist record
        """
        created_orders = []
        errors = []

        for assignation in distribution_table.supply_point_assignation_ids:
            try:
                order = self._create_single_sale_order(
                    assignation, pack_template, pricelist
                )
                created_orders.append(order)
            except Exception as e:
                partner_name = assignation.supply_point_id.partner_id.name
                errors.append(f"{partner_name}: {str(e)}")

        if errors:
            # Rollback created orders if there were errors
            for order in created_orders:
                try:
                    order.unlink()
                except Exception:
                    pass  # Best effort cleanup

            raise ValidationError(
                _("Errors creating sale orders:\n{errors}").format(
                    errors="\n".join(errors)
                )
            )

    def _create_single_sale_order(self, assignation, pack_template, pricelist):
        """
        Create a single sale order for a participant

        Args:
            assignation: Supply point assignation record
            pack_template: Pack template record
            pricelist: Pricelist record

        Returns:
            sale.order: Created sale order
        """
        # Get inscription for this assignation
        inscription = self.selfconsumption_id.inscription_ids.filtered(
            lambda i: i.partner_id == assignation.supply_point_id.partner_id
        )

        if not inscription:
            raise ValidationError(
                _("No inscription found for partner '{partner}'").format(
                    partner=assignation.supply_point_id.partner_id.name
                )
            )

        # Prepare sale order metadata
        so_metadata = self._prepare_sale_order_metadata(assignation, inscription)

        # Create sale order using component
        with sale_order_utils(self.env) as component:
            return component.create_service_invoicing_sale_order(
                inscription.partner_id,
                pack_template,
                pricelist,
                False,  # No specific date
                fields.Date.today(),
                CONTRACT_ACTION_ACTIVATE,
                "active_selfconsumption_contract",
                so_metadata,
            )

    def _prepare_sale_order_metadata(self, assignation, inscription):
        """
        Prepare metadata for sale order creation

        Args:
            assignation: Supply point assignation record

        Returns:
            dict: Sale order metadata
        """
        return {
            "selfconsumption_id": self.selfconsumption_id.id,
            "supply_point_id": assignation.supply_point_id.id,
            "supply_point_assignation_id": assignation.id,
            "recurring_interval": self.recurring_interval,
            "recurring_rule_type": self.recurring_rule_type,
            "recurring_invoicing_type": self.recurring_invoicing_type,
            "project_id": self.selfconsumption_id.id,
            "company_id": self.selfconsumption_id.company_id.id,
            "mandate_id": inscription.mandate_id.id if inscription.mandate_id else None,
        }

    # Project update methods
    def _update_project_configuration(self, pack_template, pricelist):
        """
        Update project with invoicing configuration

        Args:
            pack_template: Pack template record
            pricelist: Pricelist record
        """
        update_data = {
            "invoicing_mode": self.invoicing_mode,
            "product_id": pack_template.product_variant_id.id,
            "recurring_rule_type": self.recurring_rule_type,
            "recurring_interval": self.recurring_interval,
            "recurring_invoicing_type": self.recurring_invoicing_type,
            "pricelist_id": pricelist.id,
        }

        self.selfconsumption_id.write(update_data)

    # Main action method
    def create_contract_template(self):
        """
        Create contract template and configure invoicing

        Main method that orchestrates the entire contract template
        creation process including validation, product setup,
        pricelist creation, and sale order generation.

        Returns:
            dict: Action to close the wizard
        """
        self.ensure_one()

        # Validate wizard data
        self._validate_wizard_data()

        # Get and validate distribution table
        distribution_table = self._validate_distribution_table()

        # Validate mandates
        self._validate_mandates(distribution_table)

        # Get product references
        product_template, pack_template = self._get_product_references()

        # Create pricelist
        pricelist = self._create_pricelist(product_template)

        try:
            # Create sale orders for all participants
            self._create_sale_orders(distribution_table, pack_template, pricelist)

            # Update project configuration
            self._update_project_configuration(pack_template, pricelist)
        except Exception as e:
            # Cleanup pricelist if sale order creation fails
            try:
                pricelist.unlink()
            except Exception:
                pass  # Best effort cleanup
            raise e

        return {
            "type": "ir.actions.act_window_close",
        }

    # Utility methods
    def get_wizard_summary(self):
        """
        Get summary information about the wizard configuration

        Returns:
            dict: Summary information
        """
        self.ensure_one()

        return {
            "project_name": self.selfconsumption_id.name
            if self.selfconsumption_id
            else None,
            "invoicing_mode": self.invoicing_mode,
            "price": self.price,
            "recurring_rule": self.recurring_rule_type,
            "recurring_interval": self.recurring_interval,
            "has_distribution_table": bool(
                self.selfconsumption_id
                and self.selfconsumption_id.distribution_table_ids.filtered(
                    lambda dt: dt.state == DISTRIBUTION_STATE_PROCESS
                )
            ),
        }

    def preview_configuration(self):
        """
        Preview the configuration without creating contracts

        Returns:
            dict: Configuration preview information
        """
        self.ensure_one()

        try:
            self._validate_wizard_data()
            distribution_table = self._validate_distribution_table()

            participant_count = len(distribution_table.supply_point_assignation_ids)

            return {
                "valid_configuration": True,
                "participant_count": participant_count,
                "total_estimated_cost": self.price * participant_count,
                "invoicing_mode_display": dict(
                    SELFCONSUMPTION_INVOICING_MODE_VALUES
                ).get(self.invoicing_mode),
                "recurring_description": f"Every {self.recurring_interval} {self.recurring_rule_type}",
            }
        except ValidationError as e:
            return {
                "valid_configuration": False,
                "error_message": str(e),
            }
