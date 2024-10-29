import json

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    payment_date = fields.Date(compute="_compute_payment_date", store=False)

    def _compute_payment_date(self):
        for record in self:
            dates = []
            for payment_info in json.loads(record.invoice_payments_widget).get(
                "content", []
            ):
                dates.append(payment_info.get("date", ""))
            if dates:
                dates.sort()
                record.payment_date = dates[0]
