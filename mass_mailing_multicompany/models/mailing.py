from odoo import fields, models


class MassMailing(models.Model):
    _name = "mailing.mailing"
    _inherit = "mailing.mailing"
    # _inherit = ["multi.company.abstract", "mailing.mailing"]

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
