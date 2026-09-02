from dateutil.relativedelta import relativedelta
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities.config import DISPLAY_DATE_FORMAT
from odoo.addons.energy_communities.utils import contract_utils

from ..config import (
    MIN_POWER_VALUE,
    RECURRING_INVOICING_TYPE_POSTPAID,
    RECURRING_INVOICING_TYPE_PREPAID,
    SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED,
)


class SetNewDistributionTableWizard(models.TransientModel):
    """
    Wizard to set a new distribution table with a chosen execution date.

    For post-paid energy-delivered projects, a replacement in the middle of
    the next invoicing period also generates draft invoices for the stub
    (period start -> day before the replacement) using the existing
    invoicing wizard, then recreates contracts via contract.utils.
    """

    _name = "energy_selfconsumption.set_new_distribution_table.wizard"
    _description = "Set New Distribution Table Wizard"

    selfconsumption_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption",
        string="Self-consumption Project",
        required=True,
        readonly=True,
        help="Self-consumption project where the distribution table will be set",
    )
    execution_date = fields.Date(
        string="Effective replacement execution date",
        required=True,
        default=fields.Date.context_today,
        help="First day on which the new distribution table is operative",
    )
    power = fields.Float(
        string="Total Energy Generated (kWh)",
        help="Energy generated from the start of the period until the day before the replacement",
    )
    next_period_date_start = fields.Date(
        string="Start",
        compute="_compute_period_case",
        readonly=True,
        help="Start date of the next invoicing period",
    )
    next_period_date_end = fields.Date(
        string="End",
        compute="_compute_period_case",
        readonly=True,
        help="End date of the next invoicing period",
    )
    invoice_until_date = fields.Date(
        string="Invoice until",
        compute="_compute_period_case",
        readonly=True,
        help="Last day invoiced with the outgoing table (day before the replacement)",
    )
    invoicing_days = fields.Integer(
        string="Days to invoice",
        compute="_compute_period_case",
        readonly=True,
    )
    show_advance_invoicing = fields.Boolean(
        string="Show Advance Invoicing",
        compute="_compute_period_case",
        readonly=True,
    )
    show_period_start_note = fields.Boolean(
        string="Show Period Start Note",
        compute="_compute_period_case",
        readonly=True,
    )
    advance_invoicing_notice = fields.Text(
        string="Advance Invoicing Notice",
        compute="_compute_period_case",
        readonly=True,
    )
    period_start_note = fields.Text(
        string="Period Start Note",
        compute="_compute_period_case",
        readonly=True,
    )
    show_range_info_notice = fields.Boolean(
        string="Show Range Info Notice",
        compute="_compute_period_case",
        readonly=True,
    )
    range_info_notice = fields.Html(
        string="Range Information Notice",
        compute="_compute_period_case",
        readonly=True,
        sanitize=True,
    )
    show_out_of_range_notice = fields.Boolean(
        string="Show Out of Range Notice",
        compute="_compute_period_case",
        readonly=True,
    )
    out_of_range_notice = fields.Html(
        string="Out of Range Notice",
        compute="_compute_period_case",
        readonly=True,
        sanitize=True,
    )

    @api.depends("selfconsumption_id", "execution_date")
    def _compute_period_case(self):
        for record in self:
            period_start, period_end = record._get_next_invoicing_period()
            record.next_period_date_start = period_start
            record.next_period_date_end = period_end
            record.invoice_until_date = False
            record.invoicing_days = 0
            record.show_advance_invoicing = False
            record.show_period_start_note = False
            record.advance_invoicing_notice = False
            record.period_start_note = False
            range_info = record._get_range_info_notice()
            record.range_info_notice = record._to_bold_html(range_info)
            record.show_range_info_notice = bool(range_info)
            record.out_of_range_notice = False
            record.show_out_of_range_notice = False
            range_start, range_end = record._get_allowed_execution_date_range()
            if (
                record.execution_date
                and range_start
                and range_end
                and not (range_start <= record.execution_date <= range_end)
            ):
                record.out_of_range_notice = record._to_bold_html(
                    record._get_execution_date_out_of_range_message(),
                    danger=True,
                )
                record.show_out_of_range_notice = True
            if not record.execution_date or not period_start or not period_end:
                continue
            if not record._is_postpaid_energy_delivered():
                continue
            if period_start < record.execution_date <= period_end:
                record.show_advance_invoicing = True
                record.invoice_until_date = record.execution_date - relativedelta(
                    days=1
                )
                record.invoicing_days = (
                    record.invoice_until_date - period_start
                ).days + 1
                record.advance_invoicing_notice = _(
                    "Replacing the current table on a given date implies invoicing "
                    "the energy generated, until the day before that date, to its CUPS."
                )
            elif record.execution_date == period_start:
                record.show_period_start_note = True
                record.period_start_note = _(
                    "Informative note: Since the effective replacement date coincides "
                    "with the first day of the next period to invoice (%(period_start)s "
                    "to %(period_end)s), when you use the post-paid invoicing wizard at "
                    "the end of the period, the energy produced in that period will be "
                    "invoiced only and entirely to the CUPS included in the new table."
                ) % {
                    "period_start": period_start.strftime(DISPLAY_DATE_FORMAT),
                    "period_end": period_end.strftime(DISPLAY_DATE_FORMAT),
                }

    def _get_reference_contract(self):
        self.ensure_one()
        if not self.selfconsumption_id:
            return self.env["contract.contract"]
        return self.selfconsumption_id.get_active_contracts()[:1]

    def _get_next_invoicing_period(self):
        self.ensure_one()
        contract = self._get_reference_contract()
        if not contract:
            return False, False
        return contract.next_period_date_start, contract.next_period_date_end

    def _is_postpaid_energy_delivered(self):
        self.ensure_one()
        project = self.selfconsumption_id
        if not project:
            return False
        contract = self._get_reference_contract()
        return bool(
            project.invoicing_mode == SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED
            and contract
            and contract.recurring_invoicing_type == RECURRING_INVOICING_TYPE_POSTPAID
        )

    def _is_prepaid(self):
        self.ensure_one()
        contract = self._get_reference_contract()
        return bool(
            contract
            and contract.recurring_invoicing_type == RECURRING_INVOICING_TYPE_PREPAID
        )

    def _format_period_dates(self, range_start=None, range_end=None):
        self.ensure_one()
        if range_start is None or range_end is None:
            range_start, range_end = self._get_allowed_execution_date_range()
        return {
            "period_start": range_start.strftime(DISPLAY_DATE_FORMAT)
            if range_start
            else "",
            "period_end": range_end.strftime(DISPLAY_DATE_FORMAT) if range_end else "",
        }

    def _to_bold_html(self, text, danger=False):
        """Wrap a plain-text notice so the wizard can render it as bold HTML."""
        if not text:
            return False
        if danger:
            return Markup('<p><strong class="text-danger">{}</strong></p>').format(text)
        return Markup("<p><strong>{}</strong></p>").format(text)

    def _get_range_info_notice(self):
        """Informative text shown above the execution date field."""
        self.ensure_one()
        range_start, range_end = self._get_allowed_execution_date_range()
        if not range_start or not range_end:
            return False
        dates = self._format_period_dates(range_start, range_end)
        if self._is_prepaid():
            return (
                _(
                    "The period already pre-invoiced on the contracts linked to the "
                    "current distribution table is from %(period_start)s to "
                    "%(period_end)s. The effective replacement date you select below "
                    "must be within this range."
                )
                % dates
            )
        return (
            _(
                "The next invoicing period planned on the contracts linked to the "
                "current distribution table is from %(period_start)s to "
                "%(period_end)s. The effective replacement date you select below "
                "must be within this range."
            )
            % dates
        )

    def action_confirm(self):
        """Confirm and set the new distribution table using the selected date."""
        self.ensure_one()
        if not self.selfconsumption_id:
            raise ValidationError(_("No self-consumption project selected"))
        if not self.execution_date:
            raise ValidationError(_("Distribution table change date is required"))

        self.selfconsumption_id.check_dates_contract()
        self._validate_execution_date()

        original_recurring_next_date = False
        reference_contract = self._get_reference_contract()
        if reference_contract:
            original_recurring_next_date = reference_contract.recurring_next_date

        if self.show_advance_invoicing:
            self._invoice_outgoing_table_until_replacement()

        self.selfconsumption_id.set_new_distribution_table(
            execution_date=self.execution_date,
            period_recurring_next_date=original_recurring_next_date,
        )
        return {"type": "ir.actions.act_window_close"}

    def _validate_execution_date(self):
        """Ensure the replacement date is inside the allowed invoicing period."""
        self.ensure_one()
        range_start, range_end = self._get_allowed_execution_date_range()
        if not range_start or not range_end:
            return
        if not (range_start <= self.execution_date <= range_end):
            raise ValidationError(self._get_execution_date_out_of_range_message())

    def _get_allowed_execution_date_range(self):
        """Return the date range in which a table replacement is allowed."""
        self.ensure_one()
        contract = self._get_reference_contract()
        if not contract:
            return False, False
        if (
            contract.recurring_invoicing_type == RECURRING_INVOICING_TYPE_PREPAID
            and contract.last_date_invoiced
        ):
            delta = contract.get_relative_delta(
                contract.recurring_rule_type, contract.recurring_interval
            )
            period_start = contract.last_date_invoiced + relativedelta(days=1) - delta
            return period_start, contract.last_date_invoiced
        return contract.next_period_date_start, contract.next_period_date_end

    def _get_execution_date_out_of_range_message(self):
        self.ensure_one()
        dates = self._format_period_dates()
        if self._is_prepaid():
            return (
                _(
                    "You cannot run a distribution table replacement outside the last "
                    "period already pre-invoiced on the contracts (%(period_start)s to "
                    "%(period_end)s)"
                )
                % dates
            )
        return (
            _(
                "You cannot run a distribution table replacement outside the next "
                "invoicing period planned on the contracts (%(period_start)s to %(period_end)s)"
            )
            % dates
        )

    def _invoice_outgoing_table_until_replacement(self):
        """Invoice current contracts for the stub period using InvoicingWizard."""
        self.ensure_one()
        if self.power is not False and self.power <= MIN_POWER_VALUE:
            raise ValidationError(
                _("The energy generated must be greater than {min_value} kWh").format(
                    min_value=MIN_POWER_VALUE
                )
            )
        contracts = self.selfconsumption_id.get_active_contracts()
        if not contracts:
            return
        period_end = self.execution_date - relativedelta(days=1)
        self._force_contracts_period_end(contracts, period_end)
        invoicing_wizard = self.env["energy_selfconsumption.invoicing.wizard"].create(
            {
                "contract_ids": [(6, 0, contracts.ids)],
                "invoicing_mode": SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED,
                "power": self.power,
            }
        )
        invoices = invoicing_wizard.with_context(
            skip_distribution_table_change_notes=True
        ).generate_invoices()
        invoice_records = self.env["account.move"].browse(
            [invoice.id if hasattr(invoice, "id") else invoice for invoice in invoices]
        )
        for invoice in invoice_records:
            note = self.with_context(
                lang=invoice.partner_id.lang or self.env.lang
            )._get_advance_invoice_section_note()
            invoice.add_distribution_table_replacement_section(note)

    def _force_contracts_period_end(self, contracts, period_end):
        """Limit the next invoicing period of contracts so it ends on period_end."""
        for contract in contracts:
            offset = contract.recurring_invoicing_offset or 0
            forced_recurring_next_date = period_end + relativedelta(days=offset)
            contract.contract_line_ids.write(
                {"recurring_next_date": forced_recurring_next_date}
            )
            with contract_utils(self.env, contract) as component:
                component.propagate_recurrency_values_to_contract()

    def _get_advance_invoice_section_note(self):
        """Build the advance-invoicing section text for a given invoice."""
        self.ensure_one()
        period_start = self.next_period_date_start
        period_end = self.invoice_until_date
        return _(
            "ATTENTION: due to a replacement of the project distribution table "
            "(with effective date of the new table on %(change_date)s), this invoice "
            "covers the energy produced from the start of the invoicing period "
            "(%(period_start)s) until the day before the replacement date "
            "(%(period_end)s), that is %(days)s days of production still using the "
            "coefficient of the initial distribution table (which will be replaced "
            "by the new one from %(change_date)s)."
        ) % {
            "change_date": self.execution_date.strftime(DISPLAY_DATE_FORMAT),
            "period_start": period_start.strftime(DISPLAY_DATE_FORMAT)
            if period_start
            else "",
            "period_end": period_end.strftime(DISPLAY_DATE_FORMAT)
            if period_end
            else "",
            "days": self.invoicing_days,
        }
