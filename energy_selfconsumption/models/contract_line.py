from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ContractLine(models.Model):
    _inherit = "contract.line"

    days_invoiced = fields.Integer(
        string="Days invoiced",
        compute="_compute_days_invoiced",
        store=True,
    )

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

    def _prepare_invoice_line(self, move_form):
        self.ensure_one()
        dates = self._get_period_to_invoice(
            self.last_date_invoiced, self.recurring_next_date
        )
        line_form = move_form.invoice_line_ids.new()
        line_form.display_type = self.display_type
        line_form.product_id = self.product_id
        invoice_line_vals = line_form._values_to_save(all_fields=True)
        name = self._insert_markers(dates[0], dates[1])

        self.days_invoiced = (
            (dates[1] - dates[0]).days + 1 if dates[0] and dates[1] else 0
        )

        invoice_line_vals.update(
            {
                "account_id": invoice_line_vals["account_id"]
                if "account_id" in invoice_line_vals and not self.display_type
                else False,
                "quantity": self._get_quantity_to_invoice(*dates),
                "product_uom_id": self.uom_id.id,
                "discount": self.discount,
                "contract_line_id": self.id,
                "sequence": self.sequence,
                "name": name,
                "analytic_account_id": self.analytic_account_id.id,
                "analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)],
                "price_unit": self.price_unit,
            }
        )
        return invoice_line_vals

    @api.depends("last_date_invoiced", "recurring_next_date")
    def _compute_days_invoiced(self):
        for record in self:
            (
                first_date_invoiced,
                last_date_invoiced,
                recurring_next_date,
            ) = record._get_period_to_invoice(
                record.last_date_invoiced,
                record.recurring_next_date,
                stop_at_date_end=True,
            )

            if not first_date_invoiced or not last_date_invoiced:
                record.days_invoiced = 0
                continue

            record.days_invoiced = (last_date_invoiced - first_date_invoiced).days + 1
