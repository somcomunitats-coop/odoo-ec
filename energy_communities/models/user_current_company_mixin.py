from odoo import api, fields, models


class UserCurrentCompanyMixin(models.AbstractModel):
    _name = "user.currentcompany.mixin"
    _description = "Get current selected company from any model"

    user_current_company = fields.Many2one(
        "res.company", compute="_compute_user_current_company", store=False
    )

    allowed_companies = fields.Many2many(
        comodel_name="res.company",
        compute="_compute_allowed_companies",
        readonly=True,
        store=False,
    )

    user_current_role = fields.Char(
        compute="_compute_user_current_role",
        store=False,
        search="_search_user_current_role",
    )

    @api.depends("company_id")
    def _compute_allowed_companies(self):
        for record in self:
            record.allowed_companies = [(5, 0, 0)]
            if "allowed_company_ids" in record.env.context:
                record.allowed_companies = record.env.context["allowed_company_ids"]

    @api.depends("company_id")
    def _compute_user_current_company(self):
        for record in self:
            record.user_current_company = self.env.company

    @api.depends("company_id")
    def _compute_user_current_role(self):
        # TODO: We don't understand why on this computed method context's active_company_ids is not defined.
        # We only get allowed_company_ids
        for record in self:
            record.user_current_role = record.get_current_role()

    def _search_user_current_role(self, operator, value):
        for record in self:
            role_id = self.get_current_role_id()
            if role_id:
                return [("id", "=", role_id.id)]
        return [("id", "=", False)]

    def get_current_company_id(self):
        return self.env.company.id

    def get_current_user(self):
        return self.env.user

    def get_current_role_id(self):
        roles = self.env.user._get_enabled_roles()
        if roles:
            return roles[0].role_id
        return False

    def get_current_role(self):
        role_id = self.get_current_role_id()
        if role_id:
            return role_id.code
        return False

    def _max_priority_role_line(self, role_lines):
        if role_lines:
            selected_role_line = role_lines[0]
            for role_line in role_lines[1:]:
                if role_line.role_id.priority < selected_role_line.role_id.priority:
                    selected_role_line = role_line
            return selected_role_line
        return self.env["res.users.role.line"]
