from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ContractLine(models.Model):
    _inherit = "contract.line"

    days_invoiced = fields.Integer(
        string="Days invoiced",
        compute="_compute_days_invoiced",
        store=True,
    )
    main_line = fields.Boolean("Main line", default=False)
    # This validation is raised when writing date_start on the contract and recurring_next_date is yet not computed
    # Fixed by just checking when the recurrence is at line level (line_recurrence)
    # TODO create a PR to OCA fixing this

    @api.constrains("main_line")
    def _check_only_one_main_line(self):
        for line in self:
            contract_lines = line.contract_id.contract_line_ids
            main_lines = contract_lines.filtered(lambda l: l.main_line)
            if len(main_lines) > 1:
                raise ValidationError("There can only be one main line per contract.")

    @api.constrains("recurring_next_date", "date_start")
    def _check_recurring_next_date_start_date(self):
        for line in self:
            if line.display_type == "line_section" or not line.recurring_next_date:
                continue
            if (
                line.contract_id.line_recurrence
                and line.date_start
                and line.recurring_next_date
            ):
                if line.date_start > line.recurring_next_date:
                    raise ValidationError(
                        _(
                            "You can't have a date of next invoice anterior "
                            "to the start of the contract line '%s'"
                        )
                        % line.name
                    )

    @api.depends("last_date_invoiced", "recurring_next_date")
    def _compute_days_invoiced(self):
        for record in self:
            (
                first_date_invoiced,
                last_date_invoiced,
                _,  # recurring_next_date
            ) = record._get_period_to_invoice(
                record.last_date_invoiced,
                record.recurring_next_date,
                stop_at_date_end=True,
            )

            record.days_invoiced = (
                (last_date_invoiced - first_date_invoiced).days + 1 if first_date_invoiced and last_date_invoiced else 0
            )
