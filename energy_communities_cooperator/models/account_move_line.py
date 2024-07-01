from odoo import _, api, fields, models


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = "account.move.line"

    voluntary_share_return_start_date_period = fields.Date(string="Period start date")
    voluntary_share_return_end_date_period = fields.Date(string="Period end date")
    voluntary_share_contribution = fields.Float(string="Contribution")
    voluntary_share_interest = fields.Float(string="Interest")
