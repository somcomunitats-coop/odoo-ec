from odoo import api, fields, models


class MailComposeMessage(models.TransientModel):
    _name = "mail.compose.message"
    _inherit = "mail.compose.message"

    user_current_company = fields.Many2one(
        "res.company", compute="_compute_user_current_company", store=False
    )

    @api.depends("campaign_id")
    def _compute_user_current_company(self):
        for record in self:
            record.user_current_company = self.env.user.user_current_company
