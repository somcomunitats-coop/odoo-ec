from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    same_dates = fields.Boolean(
        string="Payment Date = Invoice Date",
        store=True,
        readonly=True,
        compute="_compute_same_dates",
        help="True if payment date is the same date as invoice date",
    )
