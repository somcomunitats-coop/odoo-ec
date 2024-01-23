from odoo import api, fields, models


class UserCurrentCompanyMixin(models.AbstractModel):
    _name = "user.currentcompany.mixin"
    _description = "Get current selected company from any model"

    user_current_company = fields.Many2one(
        "res.company", compute="_compute_user_current_company", store=False
    )

    allowed_companies = fields.Many2many(
        compute="_compute_allowed_companies",
        readonly=True,
        store=False,
    )

    def _compute_allowed_companies(self):
        for record in self:
            record.allowed_companies = record.env.context["allowed_company_ids"]

    def _compute_user_current_company(self):
        for record in self:
            record.user_current_company = record.get_user_current_company()

    def get_user_current_company(self):
        return self.get_current_company()

    def get_current_role(self):
        current_company = self.get_current_company()
        current_role_lines = self.role_line_ids.filtered(
            lambda role_line: role_line.company_id.id == current_company
        )
        if current_role_lines:
            return current_role_lines[
                0
            ].role_id.code  # avoid misconfiguration, only one role per company TODO: constrain company_id on role to avoid this misconfigurations
        else:
            admin_role_lines = self.role_line_ids.filtered(
                lambda role_line: role_line.role_id.code == "role_platform_admin"
            )
            if admin_role_lines:
                return "role_platform_admin"
        return False

    def get_current_company(self):
        return self.env.context["allowed_company_ids"][0]
