from odoo import _, fields, models

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
        string=_("Invoicing Mode"),
        default="power_acquired",
        required=True,
    )

    price = fields.Float(required=True)

    recurrence_interval = fields.Integer(
        default=1,
        string=_("Invoice Every"),
        help=_("Invoice every (Days/Week/Month/Year)"),
    )
    recurring_rule_type = fields.Selection(
        RULE_TYPE_OPTIONS,
        default="monthlylastday",
        string=_("Recurrence"),
        help=_("Specify Interval for automatic invoice generation."),
    )
    selfconsumption_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption", readonly=True
    )

    def save_data_to_selfconsumption(self):
        # Create product
        product_id = self.env["product.product"].create(
            {
                "name": f"{self.invoicing_mode[1]} - {self.selfconsumption_id.name}",
                "lst_price": self.price,
                "company_id": self.env.company.id,
                "project_id": self.selfconsumption_id.project_id.id,
            }
        )

        # Create contract formula
        # TODO:actualizar formula energy_delivered y energy_delivered_variable.
        #  4.Contract.template (en ivoicing --> configuracion --> create contract tmplate

        if self.invoicing_mode == "power_acquired":
            self.env["contract.line.qty.formula"].create(
                {
                    "name": _("Formula - %s") % (self.selfconsumption_id.name),
                    "code": f"""
days_timedelta = line.next_period_date_end - line.next_period_date_start
if days_timedelta:
  # Add one so it counts the same day too (month = 29 + 1)
  days_between = days_timedelta.days + 1
else:
  days_between = 0
result = line.supply_point_assignation_id.distribution_table_id.selfconsumption_project_id.power * line.supply_point_assignation_id.coefficient * {self.price} * days_between
""",
                }
            )
        elif self.invoicing_mode == "energy_delivered":
            self.env["contract.line.qty.formula"].create(
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
            self.env["contract.line.qty.formula"].create(
                {
                    "name": _("Formula - %s") % (self.selfconsumption_id.name),
                    "code": """
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

        self.selfconsumption_id.write(
            {
                "invoicing_mode": self.invoicing_mode,
                "product_id": product_id,
            }
        )

        return {
            "type": "ir.actions.act_window_close",
        }
