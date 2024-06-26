from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class VoluntaryShareInterestReturn(models.Model):
    _name = "voluntary.share.interest.return"
    _inherit = ["mail.thread"]

    name = fields.Char(string="Name")
    start_date_period = fields.Date(string="Period start date")
    end_date_period = fields.Date(string="Period end date")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    account_move_ids = fields.One2many(
        "account.move", "voluntary_share_interest_return_id", string="Moves"
    )
