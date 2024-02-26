from odoo import api, fields, models


class PartnerMailListWizard(models.TransientModel):
    _name = "partner.mail.list.wizard"
    _inherit = "partner.mail.list.wizard"

    user_current_company = fields.Many2one(
        "res.company", compute="_compute_user_current_company", store=False
    )

    @api.depends("mail_list_id")
    def _compute_user_current_company(self):
        for record in self:
            record.user_current_company = self.env.user.user_current_company
