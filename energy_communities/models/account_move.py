from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    payment_date = fields.Date(compute="_compute_payment_date", store=False)

    def _compute_payment_date(self):
        for record in self:
            dates = []
            record.payment_date = False
            if record.invoice_payments_widget:
                for payment_info in record.invoice_payments_widget.get("content", []):
                    if payment_info:
                        dates.append(payment_info.get("date", ""))
            if dates:
                dates.sort()
                record.payment_date = dates[0]
