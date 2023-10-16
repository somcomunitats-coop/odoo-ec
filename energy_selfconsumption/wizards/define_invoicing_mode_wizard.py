from odoo import _, fields, models
from odoo.exceptions import UserError

from ..models.selfconsumption import INVOICING_VALUES


class ContractGenerationWizard(models.TransientModel):
    _name = "energy_selfconsumption.define_invoicing_mode.wizard"

    RULE_TYPE_OPTIONS = [
        ("daily", _("Day(s)")),
        ("weekly", _("Week(s)")),
        ("monthly", _("Month(s)")),
        ("monthlylastday", _("Month(s) last day")),
        ("quarterly", _("Quarter(s)")),
        ("semesterly", _("Semester(s)")),
        ("yearly", _("Year(s)")),
    ]

    invoicing_mode = fields.Selection(
        INVOICING_VALUES,
        string="Invoicing Mode",
        default="power_acquired",
        required=True,
    )

    price = fields.Float(required=True)

    recurrence_interval = fields.Integer(
        default=1,
        string="Invoice Every",
        required=True,
        help=_("Invoice every (Days/Week/Month/Year)"),
    )
    recurring_rule_type = fields.Selection(
        RULE_TYPE_OPTIONS,
        default="monthlylastday",
        string="Recurrence",
        required=True,
        help=_("Specify Interval for automatic invoice generation."),
    )
    selfconsumption_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption", readonly=True
    )

    def save_data_to_selfconsumption(self):
        if self.invoicing_mode == "energy_delivered_variable":
            raise UserError("This invoicing mode is not yet implemented")

        # Create product
        product_id = self.env["product.product"].create(
            {
                "name": self.selfconsumption_id.name,
                "lst_price": self.price,
                "company_id": self.env.company.id,
                "project_id": self.selfconsumption_id.project_id.id,
            }
        )

        # Create contract formula
        # TODO:Update formula energy_delivered and energy_delivered_variable.
        formula_contract_id = None
        if self.invoicing_mode == "power_acquired":
            formula_contract_id = self.env["contract.line.qty.formula"].create(
                {
                    "name": _("Formula - %s") % (self.selfconsumption_id.name),
                    "code": f"""
days_timedelta = line.next_period_date_end - line.next_period_date_start
if days_timedelta:
  # Add one so it counts the same day too (month = 29 + 1)
  days_between = days_timedelta.days + 1
else:
  days_between = 0
result = line.supply_point_assignation_id.distribution_table_id.selfconsumption_project_id.power * line.supply_point_assignation_id.coefficient *  days_between
""",
                }
            )
        elif self.invoicing_mode == "energy_delivered":
            formula_contract_id = self.env["contract.line.qty.formula"].create(
                {
                    "name": _("Formula - %s") % (self.selfconsumption_id.name),
                    "code": f"""
days_timedelta = line.next_period_date_end - line.next_period_date_start
if days_timedelta:
    # Add one so it counts the same day too (month = 29 + 1)
    days_between = days_timedelta.days + 1
else:
    days_between = 0
result = line.supply_point_assignation_id.distribution_table_id.selfconsumption_project_id.power * line.supply_point_assignation_id.coefficient * days_between
""",
                }
            )
        elif self.invoicing_mode == "energy_delivered_variable":
            formula_contract_id = self.env["contract.line.qty.formula"].create(
                {
                    "name": _("Formula - %s") % (self.selfconsumption_id.name),
                    "code": f"""
days_timedelta = line.next_period_date_end - line.next_period_date_start
if days_timedelta:
    # Add one so it counts the same day too (month = 29 + 1)
    days_between = days_timedelta.days + 1
else:
    days_between = 0
result = line.supply_point_assignation_id.distribution_table_id.selfconsumption_project_id.power * line.supply_point_assignation_id.coefficient * days_between
""",
                }
            )

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
                {
                    "product_id": product_id.id,
                    "automatic_price": True,
                    "company_id": self.env.company.id,
                    "qty_type": "variable",
                    "qty_formula_id": formula_contract_id.id,
                    "name": "",
                },
            )
        ]

        contract_template_id = self.env["contract.template"].create(
            {
                "name": self.selfconsumption_id.name,
                "journal_id": journal_id.id,
                "company_id": self.env.company.id,
                "contract_line_ids": contract_line,
                "recurring_interval": self.recurrence_interval,
                "recurring_rule_type": self.recurring_rule_type,
            }
        )

        self.selfconsumption_id.write(
            {
                "invoicing_mode": self.invoicing_mode,
                "product_id": product_id,
                "contract_template_id": contract_template_id,
            }
        )

        return {
            "type": "ir.actions.act_window_close",
        }
