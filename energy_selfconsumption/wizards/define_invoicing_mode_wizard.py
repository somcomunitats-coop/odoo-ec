from odoo import _, fields, models


class ContractGenerationWizard(models.TransientModel):
    _name = "energy_selfconsumption.define_invoicing_mode.wizard"

    INVOICING_VALUES = [
        ("power_acquired", _("By power acquired")),
        ("energy_delivered", _("By energy delivered")),
        (
            "energy_delivered_hourly",
            _("For energy delivered hourly variable coefficients (CSV)"),
        ),
    ]

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
