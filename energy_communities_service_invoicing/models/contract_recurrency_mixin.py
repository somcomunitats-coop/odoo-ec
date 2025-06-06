from datetime import date

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


class ContractRecurrencyMixin(models.AbstractModel):
    _inherit = "contract.recurrency.mixin"
    _name = "contract.recurrency.mixin"

    @api.depends("next_period_date_start")
    def _compute_recurring_next_date(self):
        for record in self:
            if record.recurring_rule_mode == "fixed":
                record.recurring_next_date = record.get_next_invoice_date_fixed()
            else:
                super()._compute_recurring_next_date()

    @api.depends("last_date_invoiced", "date_start", "date_end")
    def _compute_next_period_date_start(self):
        for record in self:
            if record.recurring_rule_mode == "fixed":
                record.next_period_date_start = (
                    record.get_next_period_date_start_fixed()
                )
            else:
                super()._compute_next_period_date_start()

    @api.depends(
        "next_period_date_start",
        "recurring_invoicing_type",
        "recurring_invoicing_offset",
        "recurring_rule_type",
        "recurring_interval",
        "date_end",
        "recurring_next_date",
    )
    def _compute_next_period_date_end(self):
        for record in self:
            if record.recurring_rule_mode == "fixed":
                record.next_period_date_end = record.get_next_period_date_end_fixed()
            else:
                super()._compute_next_period_date_end()

    # TODO: All getters below are based on the fact that self.recurring_invoicing_fixed_type == "yearly"
    # We will have to add conditions if we implement other recurring_invoicing_fixed_type scenarios
    def get_next_invoice_date_fixed(self):
        if self.last_date_invoiced:
            if self.recurring_invoicing_type == "pre-paid":
                next_invoice_date = self.last_date_invoiced + relativedelta(days=+1)
            if self.recurring_invoicing_type == "post-paid":
                next_invoice_date = self.last_date_invoiced + relativedelta(
                    years=+1, days=+1
                )
        else:
            next_invoice_date = date(
                self.date_start.year,
                int(self.fixed_invoicing_month),
                int(self.fixed_invoicing_day),
            )
            if self.date_start > next_invoice_date or (
                self.date_start == next_invoice_date
                and self.recurring_invoicing_type == "post-paid"
            ):
                next_invoice_date += relativedelta(years=+1)
        return next_invoice_date

    def get_next_period_date_start_fixed(self):
        if self.last_date_invoiced:
            if self.recurring_invoicing_type == "pre-paid":
                next_period_date_start = self.last_date_invoiced + relativedelta(
                    days=+1
                )
            if self.recurring_invoicing_type == "post-paid":
                next_period_date_start = self.last_date_invoiced + relativedelta(
                    days=+1
                )
        else:
            next_period_date_start = date(
                self.date_start.year,
                int(self.fixed_invoicing_month),
                int(self.fixed_invoicing_day),
            )
            if (
                self.recurring_invoicing_type == "pre-paid"
                and self.date_start > next_period_date_start
            ):
                next_period_date_start = date(
                    (self.date_start + relativedelta(years=+1)).year,
                    int(self.fixed_invoicing_month),
                    int(self.fixed_invoicing_day),
                )
            if self.recurring_invoicing_type == "post-paid":
                if self.date_start != next_period_date_start:
                    next_period_date_start = self.date_start
        if self.date_end and next_period_date_start >= self.date_end:
            next_period_date_start = False
        return next_period_date_start

    def get_next_period_date_end_fixed(self):
        if self.last_date_invoiced:
            next_period_date_end = self.last_date_invoiced + relativedelta(years=+1)
        else:
            next_period_date_end = date(
                self.date_start.year,
                int(self.fixed_invoicing_month),
                int(self.fixed_invoicing_day),
            )
            if self.recurring_invoicing_type == "pre-paid":
                if self.date_start > next_period_date_end:
                    next_period_date_end += relativedelta(years=+1)
                if self.date_start <= next_period_date_end:
                    next_period_date_end += relativedelta(years=+1, days=-1)
            if self.recurring_invoicing_type == "post-paid":
                if self.date_start > next_period_date_end:
                    next_period_date_end += relativedelta(years=+1)
                if self.date_start < next_period_date_end:
                    next_period_date_end += relativedelta(days=-1)
                if self.date_start == next_period_date_end:
                    next_period_date_end += relativedelta(years=+1, days=-1)
        if self.date_end and next_period_date_end >= self.date_end:
            next_period_date_end = False
        return next_period_date_end
