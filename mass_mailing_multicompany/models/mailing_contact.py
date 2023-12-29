from odoo import fields, models


class MassMailingContact(models.Model):
    _name = "mailing.contact"
    _inherit = "mailing.contact"

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
