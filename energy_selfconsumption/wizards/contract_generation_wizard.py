import logging

from odoo import _, fields, models

logger = logging.getLogger(__name__)


class ContractGenerationWizard(models.TransientModel):
    _name = "energy_selfconsumption.contract_generation.wizard"

    price_energy = fields.Float(string="Price (€/kWn/day)")

    recurring_interval = fields.Integer(
        default=1,
        string="Invoice Every",
        help="Invoice every (Days/Week/Month/Year)",
    )
    recurring_rule_type = fields.Selection(
        [
            ("daily", "Day(s)"),
            ("weekly", "Week(s)"),
            ("monthly", "Month(s)"),
            ("monthlylastday", "Month(s) last day"),
            ("quarterly", "Quarter(s)"),
            ("semesterly", "Semester(s)"),
            ("yearly", "Year(s)"),
        ],
        default="monthly",
        string="Recurrence",
        help="Specify Interval for automatic invoice generation.",
    )
    selfconsumption_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption", readonly=True
    )

    def generate_contracts_button(self):
        product_id = self.env["product.product"].create(
            {
                "name": _("Energy Generated"),
                "lst_price": self.price_energy,
                "company_id": self.env.company.id,
            }
        )

        formula_contract_id = self.env["contract.line.qty.formula"].create(
            {
                "name": _("Formula - %s") % (self.selfconsumption_id.name),
                "code": "result = line.supply_point_assignation_id.distribution_table_id.selfconsumption_project_id.power * line.supply_point_assignation_id.coefficient * 30",
            }
        )

        journal_id = self.env["account.journal"].search(
            [("company_id", "=", self.env.company.id), ("type", "=", "sale")], limit=1
        )
        if not journal_id:
            raise UserWarning(_("Accounting Journal not found."))

        contract_template = self.env["contract.template"].create(
            {
                "name": _("Contract Template - %s") % self.selfconsumption_id.name,
                "company_id": self.env.company.id,
                "contract_type": "sale",
                "journal_id": journal_id.id,
                "contract_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product_id.id,
                            "company_id": self.env.company.id,
                            "qty_type": "fixed",
                            "quantity": 1,
                            "recurring_interval": self.recurring_interval,
                            "recurring_rule_type": self.recurring_rule_type,
                            "recurring_invoicing_type": "post-paid",
                            "name": _("Energy produced"),
                        },
                    )
                ],
            }
        )

        distribution_id = (
            self.selfconsumption_id.distribution_table_ids.filtered_domain(
                [("state", "=", "process")]
            )
        )
        if not distribution_id:
            raise _("There is no distribution table in proces of activation.")

        supply_point_assignation_ids = distribution_id.supply_point_assignation_ids
        partner_list = {}

        for supply_point_assignation in supply_point_assignation_ids:
            key = (
                supply_point_assignation.supply_point_id.partner_id.id,
                supply_point_assignation.owner_id.id,
            )
            if key not in partner_list:
                partner_list[key] = {
                    "parent_id": supply_point_assignation.supply_point_id.partner_id,
                    "owner_id": supply_point_assignation.owner_id,
                    "supply_point_assignation_ids": [supply_point_assignation],
                }
            else:
                partner_list[key]["supply_point_assignation_ids"].append(
                    supply_point_assignation
                )

        for key, value in partner_list.items():
            contract_lines = []
            for supply_point_assignation_id in value["supply_point_assignation_ids"]:
                contract_lines.append(
                    (
                        0,
                        0,
                        {
                            "product_id": product_id.id,
                            "automatic_price": True,
                            "company_id": self.env.company.id,
                            "qty_type": "variable",
                            "qty_formula_id": formula_contract_id.id,
                            "name": _(supply_point_assignation_id.supply_point_id.code),
                            "supply_point_assignation_id": supply_point_assignation_id.id,
                        },
                    )
                )

            self.env["contract.contract"].create(
                {
                    "name": _("Contract - %s - %s")
                    % (self.selfconsumption_id.name, value["parent_id"].name),
                    "partner_id": value["parent_id"].id,
                    "invoice_partner_id": value["parent_id"].id,
                    "journal_id": journal_id.id,
                    "recurring_interval": self.recurring_interval,
                    "recurring_rule_type": self.recurring_rule_type,
                    "recurring_invoicing_type": "post-paid",
                    "date_start": fields.date.today(),
                    "company_id": self.env.company.id,
                    "contract_line_ids": contract_lines,
                }
            )

        return True
