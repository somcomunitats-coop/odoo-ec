from odoo import api, fields, models


class MailComposeMessage(models.TransientModel):
    _name = "mail.compose.message"
    _inherit = ["mail.compose.message", "user.currentcompany.mixin"]

    @api.depends("campaign_id")
    def _compute_user_current_company(self):
        super()._compute_user_current_company()

    @api.depends("campaign_id")
    def _compute_allowed_companies(self):
        super()._compute_allowed_companies()
