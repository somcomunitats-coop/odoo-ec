from odoo import api, fields, models


class MassMailing(models.Model):
    _name = "mailing.mailing"
    _inherit = ["mailing.mailing", "user.currentcompany.mixin"]

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )

    @api.depends("company_id")
    def _compute_user_current_company(self):
        super()._compute_user_current_company()
