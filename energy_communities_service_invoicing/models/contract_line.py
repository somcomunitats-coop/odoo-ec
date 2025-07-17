from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class ContractLine(models.Model):
    _inherit = "contract.line"

    ordered_qty_type = fields.Char()
    ordered_quantity = fields.Float()
    ordered_qty_formula_id = fields.Many2one("contract.line.qty.formula")

    def _compute_allowed(self):
        super()._compute_allowed()
        for record in self:
            record.is_cancel_allowed = True

    # skip last_date_invoice update for modification action if contract is ready to start or on free plan.
    def _update_recurring_next_date(self):
        # TODO: Pay attention to original code in order to detect if method has been renamed:
        # FIXME: Change method name according to real updated field
        # e.g.: _update_last_date_invoiced()
        for record in self:
            if record.contract_id.status == "paused" or record.contract_id.is_free_pack:
                return
        super()._update_recurring_next_date()

    # overwritten method from original. We allow future invoice generation
    @api.depends(
        "display_type",
        "is_recurring_note",
        "recurring_next_date",
        "date_start",
        "date_end",
    )
    def _compute_create_invoice_visibility(self):
        # TODO: depending on the lines, and their order, some sections
        # have no meaning in certain invoices
        today = fields.Date.context_today(self)
        for rec in self:
            if (
                (not rec.display_type or rec.is_recurring_note)
                and rec.date_start
                # and today >= rec.date_start
            ):
                rec.create_invoice_visibility = bool(rec.recurring_next_date)
            else:
                rec.create_invoice_visibility = False
