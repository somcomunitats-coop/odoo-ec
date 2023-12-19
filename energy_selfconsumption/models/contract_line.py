from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ContractLine(models.Model):
    _inherit = "contract.line"

    # This validation is raised when writing date_start on the contract and recurring_next_date is yet not computed
    # Fixed by just checking when the recurrence is at line level (line_recurrence)
    # TODO create a PR to OCA fixing this
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
