from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities.utils import sale_order_utils

from ..models.selfconsumption import INVOICING_VALUES


class ContractGenerationWizard(models.TransientModel):
    _name = "energy_selfconsumption.define_invoicing_mode.wizard"
    _description = "Service to generate contract"
    _inherit = [
        "contract.recurrency.mixin",
    ]

    invoicing_mode = fields.Selection(
        INVOICING_VALUES,
        string="Invoicing Mode",
        default="power_acquired",
        required=True,
    )

    price = fields.Float(required=True)

    selfconsumption_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption", readonly=True
    )

    @api.onchange("invoicing_mode")
    def _onchange_invoicing_mode(self):
        if self.invoicing_mode == "energy_custom":
            self.recurring_rule_type = "monthly"
        else:
            self.recurring_rule_type = "monthlylastday"

    def create_contract_template(self):
        # Select product
        product_template = None
        pack = None
        if self.invoicing_mode == "power_acquired":
            product_template = self.env.ref(
                "energy_selfconsumption.product_product_power_acquired_product_template"
            )
            pack = self.env.ref(
                "energy_selfconsumption.product_product_power_acquired_product_pack_template"
            )
        elif self.invoicing_mode == "energy_delivered":
            product_template = self.env.ref(
                "energy_selfconsumption.product_product_energy_delivered_product_template"
            )
            pack = self.env.ref(
                "energy_selfconsumption.product_product_energy_delivered_product_pack_template"
            )
        elif self.invoicing_mode == "energy_custom":
            product_template = self.env.ref(
                "energy_selfconsumption.product_product_energy_custom_product_template"
            )
            pack = self.env.ref(
                "energy_selfconsumption.product_product_energy_custom_product_pack_template"
            )
        else:
            raise ValidationError(_("Invalid invoicing mode"))

        # Create pricelist
        pricelist = self.env["product.pricelist"].create(
            {
                "name": f"{self.selfconsumption_id.name} {self.invoicing_mode} Selfconsumption Pricelist",
                "company_id": self.selfconsumption_id.company_id.id,
                "currency_id": self.selfconsumption_id.company_id.currency_id.id,
                "discount_policy": "without_discount",
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "base": "standard_price",
                            "product_tmpl_id": product_template.id,
                            "product_id": product_template.product_variant_id.id,
                            "compute_price": "fixed",
                            "fixed_price": self.price,
                            "categ_id": self.env.ref(
                                "energy_selfconsumption.product_category_selfconsumption_service"
                            ).id,
                        },
                    )
                ],
            }
        )

        # Get distribution table
        distribution_id = (
            self.selfconsumption_id.distribution_table_ids.filtered_domain(
                [("state", "=", "process")]
            )
        )
        if not distribution_id:
            raise ValidationError(
                _("There is no distribution table in proces of activation.")
            )

        # Create sale order
        for supply_point_assignation in distribution_id.supply_point_assignation_ids:
            inscription_id = self.selfconsumption_id.inscription_ids.filtered_domain(
                [
                    (
                        "partner_id",
                        "=",
                        supply_point_assignation.supply_point_id.partner_id.id,
                    )
                ]
            )

            if not inscription_id.mandate_id:
                raise ValidationError(
                    _("Mandate not found for {partner}").format(
                        partner=supply_point_assignation.supply_point_id.partner_id.name
                    )
                )
            with sale_order_utils(self.env) as component:
                so_metadata = {
                    "selfconsumption_id": self.selfconsumption_id.id,
                    "supply_point_id": supply_point_assignation.supply_point_id.id,
                    "supply_point_assignation_id": supply_point_assignation.id,
                    "recurring_interval": self.recurring_interval,
                    "recurring_rule_type": self.recurring_rule_type,
                    "recurring_invoicing_type": self.recurring_invoicing_type,
                    "project_id": self.selfconsumption_id.id,
                    "company_id": self.selfconsumption_id.company_id.id,
                }
                # config journal if defined
                sale_journal_id = pack.categ_id.with_context(
                    company_id=self.selfconsumption_id.company_id.id
                ).service_invoicing_sale_journal_id
                if sale_journal_id:
                    so_metadata["journal_id"] = sale_journal_id.id
                component.create_service_invoicing_sale_order(
                    inscription_id.partner_id,
                    pack,
                    pricelist,
                    False,
                    fields.Date.today(),
                    "activate",
                    "active_selfconsumption_contract",
                    so_metadata,
                )
        self.selfconsumption_id.write(
            {
                "invoicing_mode": self.invoicing_mode,
                "product_id": pack.product_variant_id.id,
                "recurring_rule_type": self.recurring_rule_type,
                "recurring_interval": self.recurring_interval,
                "recurring_invoicing_type": self.recurring_invoicing_type,
                "pricelist_id": pricelist.id,
            }
        )

        return {
            "type": "ir.actions.act_window_close",
        }
