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

    user_current_role = fields.Char(compute="_compute_user_current_role", store=False)

    @api.depends("company_id")
    def _compute_allowed_companies(self):
        for record in self:
            record.allowed_companies = record.env.context["allowed_company_ids"]

    @api.depends("company_id")
    def _compute_user_current_company(self):
        for record in self:
            record.user_current_company = self.env.company

    @api.depends("company_id")
    def _compute_user_current_role(self):
        for record in self:
            record.user_current_role = record.get_current_role()

    def get_current_company_id(self):
        return self.env.company.id

    def get_current_user(self):
        return self.env.user

    def get_current_role(self):
        current_company_id = self.get_current_company_id()
        current_user = self.get_current_user()
        current_role_lines = current_user.role_line_ids.filtered(
            lambda role_line: role_line.company_id.id == current_company_id
        )
        if current_role_lines:
            return current_role_lines[
                0
            ].role_id.code  # avoid misconfiguration, only one role per company TODO: constrain company_id on role to avoid this misconfigurations
        else:
            admin_role_lines = current_user.role_line_ids.filtered(
                lambda role_line: role_line.role_id.code == "role_platform_admin"
            )
            if admin_role_lines:
                return "role_platform_admin"
        return False
