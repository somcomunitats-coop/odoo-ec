from odoo import fields, models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    company_id = fields.Many2one(required=False, default=lambda self: self.env.company)
