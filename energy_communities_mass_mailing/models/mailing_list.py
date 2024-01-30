from odoo import api, fields, models


class MassMailingList(models.Model):
    _name = "mailing.list"
    _inherit = ["mailing.list", "user.currentcompany.mixin"]

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
