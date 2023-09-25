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

        return True
