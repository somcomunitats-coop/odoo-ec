from odoo import api, fields, models


class PartnerMailListWizard(models.TransientModel):
    _name = "partner.mail.list.wizard"
    _inherit = ["partner.mail.list.wizard", "user.currentcompany.mixin"]

    @api.depends("mail_list_id")
    def _compute_user_current_company(self):
        super()._compute_user_current_company()
