from odoo import api, fields, models


class UserCurrentCompanyMixin(models.AbstractModel):
    _name = "user.currentcompany.mixin"
    _description = "Get current selected company from any model"

    user_current_company = fields.Many2one(
        "res.company", compute="_compute_user_current_company", store=False
    )

    def _compute_user_current_company(self):
        for record in self:
            record.user_current_company = record.get_user_current_company()

    def get_user_current_company(self):
        return self.env.user.get_current_company()
