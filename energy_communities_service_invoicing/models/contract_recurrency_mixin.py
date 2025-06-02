from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..utils import (
    get_month_selection_options,
    get_monthdays_selection_options,
    validate_monthday_date,
)


class ContractRecurrencyBasicMixin(models.AbstractModel):
    _inherit = "contract.recurrency.basic.mixin"
    _name = "contract.recurrency.basic.mixin"

    recurring_rule_mode = fields.Selection(
        [
            ("interval", "Interval based recurrency"),
            ("fixed", "Fixed date based recurrency"),
        ],
        default="interval",
        string="Recurrence mode",
        required=True,
    )
    # TODO: We must implement other interval recurrency. (Monthly, Quaterly,...)
    recurring_invoicing_fixed_type = fields.Selection(
        [
            ("yearly", "Year(s)"),
        ],
        default="yearly",
        string="Fixed invoice every",
    )
    fixed_invoicing_day = fields.Selection(
        get_monthdays_selection_options(), string="Fixed invoicing day"
    )
    fixed_invoicing_month = fields.Selection(
        get_month_selection_options(), string="Fixed invoicing month"
    )

    @api.constrains("fixed_invoicing_day", "fixed_invoicing_month")
    def _constrains_fixed_invoicing_date(self):
        for record in self:
            # validate a correct date was introduced
            if record.recurring_invoicing_fixed_type == "monthly":
                if int(record.fixed_invoicing_day) > 28:
                    raise ValidationError(
                        "In order to invoice always same day of a month the value must be lower or equal than 28"
                    )
            if record.recurring_invoicing_fixed_type == "yearly":
                validate_monthday_date(
                    record.fixed_invoicing_month, record.fixed_invoicing_day
                )
