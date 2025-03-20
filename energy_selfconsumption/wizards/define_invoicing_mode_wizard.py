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
                "company_id": self.env.company.id,
                "currency_id": self.env.company.currency_id.id,
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

        # Search accounting journal
        journal_id = self.env["account.journal"].search(
            [("company_id", "=", self.env.company.id), ("type", "=", "sale")], limit=1
        )
        if not journal_id:
            raise UserWarning(_("Accounting Journal not found."))

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
                component.create_service_invoicing_initial(
                    self.env,
                    inscription_id.partner_id,
                    pack.id,
                    pricelist.id,
                    fields.Date.today(),
                    "create",
                    executed_action_description="none",
                    payment_mode_id=False,
                    metadata={
                        "selfconsumption_id": self.selfconsumption_id.id,
                        "supply_point_id": supply_point_assignation.supply_point_id.id,
                        "recurring_interval": self.recurring_interval,
                        "recurring_rule_type": self.recurring_rule_type,
                        "journal_id": journal_id.id,
                    },
                )

        self.selfconsumption_id.write(
            {
                "invoicing_mode": self.invoicing_mode,
                "product_id": pack.id,
                "contract_template_id": pack.property_contract_template_id.id,
            }
        )

        return {
            "type": "ir.actions.act_window_close",
        }

    def _prepare_product_values(self):
        account_income_xml_id = "l10n_es.%i_account_common_7050" % self.env.company.id
        account_income_id = self.env.ref(account_income_xml_id)
        account_tax_xml_id = (
            "l10n_es.%i_account_tax_template_s_iva21s" % self.env.company.id
        )
        account_tax_id = self.env.ref(account_tax_xml_id)
        uom_kw_id = self.env.ref("energy_project.kw_uom")
        if self.invoicing_mode == "energy_custom":
            uom_kw_id = self.env.ref("energy_project.kwh_uom")
        return {
            "name": self.selfconsumption_id.name,
            "type": "service",
            "lst_price": self.price,
            "company_id": self.env.company.id,
            "property_account_income_id": account_income_id.id,
            "taxes_id": [account_tax_id.id],
            "sale_ok": True,
            "purchase_ok": False,
            "uom_id": uom_kw_id.id,
            "uom_po_id": uom_kw_id.id,
        }

    def _prepare_contract_template_values(self, journal_id, contract_line):
        return {
            "name": self.selfconsumption_id.name,
            "journal_id": journal_id.id,
            "company_id": self.env.company.id,
            "contract_line_ids": contract_line,
            "recurring_interval": self.recurring_interval,
            "recurring_rule_type": self.recurring_rule_type,
            "recurring_invoicing_type": "post-paid",
        }

    def _prepare_contract_line_template_values(self, product_id, formula_contract_id):
        return {
            "product_id": product_id.id,
            "automatic_price": False,
            "company_id": self.env.company.id,
            "qty_type": self._get_qty_type(),
            "qty_formula_id": self._get_qty_formula_id(formula_contract_id),
            "quantity": self._get_quantity(),
            "uom_id": product_id.uom_id.id,
            "name": _(
                """CUPS: {code}\nOwner: {owner_id}\nInvoicing period: #START# - #END#\n"""
            ),
        }

    def _get_qty_type(self):
        if self.invoicing_mode == "energy_custom":
            return "fixed"
        else:
            return "variable"

    def _get_qty_formula_id(self, formula_contract_id):
        if self.invoicing_mode == "energy_custom":
            return False
        else:
            return formula_contract_id.id

    def _get_quantity(self):
        if self.invoicing_mode == "energy_custom":
            return 0
        else:
            return 1

    def save_data_to_selfconsumption(self):
        # Create product
        product_id = self.env["product.product"].create(self._prepare_product_values())

        formula_contract_id = None
        if self.invoicing_mode == "power_acquired":
            formula_contract_id = self.env.ref(
                "energy_selfconsumption.power_acquired_formula"
            )
        elif self.invoicing_mode == "energy_delivered":
            formula_contract_id = self.env.ref(
                "energy_selfconsumption.energy_delivered_formula"
            )
        elif self.invoicing_mode == "energy_custom":
            formula_contract_id = False

        # Search accounting journal
        journal_id = self.env["account.journal"].search(
            [("company_id", "=", self.env.company.id), ("type", "=", "sale")], limit=1
        )
        if not journal_id:
            raise UserWarning(_("Accounting Journal not found."))

        # Create Contract Template
        contract_line = [
            (
                0,
                0,
                self._prepare_contract_line_template_values(
                    product_id, formula_contract_id
                ),
            )
        ]

        contract_template_id = self.env["contract.template"].create(
            self._prepare_contract_template_values(journal_id, contract_line)
        )

        product_id.write({"contract_template_id": contract_template_id.id})

        self.selfconsumption_id.write(
            {
                "invoicing_mode": self.invoicing_mode,
                "product_id": product_id,
            }
        )

        return {
            "type": "ir.actions.act_window_close",
        }
