from odoo import fields, models


class MassMailingList(models.Model):
    _name = "mailing.list"
    _inherit = "mailing.list"

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
