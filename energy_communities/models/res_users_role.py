from odoo import fields, models


class ResUsersRole(models.Model):
    _inherit = "res.users.role"

    code = fields.Char(string="Code")
    priority = fields.Integer(
        string="Priority", compute="_compute_priority_and_available_roles"
    )
    available_role_ids = fields.Many2many(
        "res.users.role",
        "res_users_role_rel",
        "role_id",
        "available_role_id",
        string="Available roles",
        compute="_compute_priority_and_available_roles",
    )

    def _compute_priority_and_available_roles(self):
        available_roles = [
            (4, self.env.ref("energy_communities.role_ce_manager").id),
            (4, self.env.ref("energy_communities.role_ce_admin").id),
            (4, self.env.ref("energy_communities.role_ce_member").id),
            (4, self.env.ref("energy_communities.role_platform_admin").id),
        ]
        internal_user_extra_roles = [
            (4, self.env.ref("energy_communities.role_platform_admin").id),
            (4, self.env.ref("energy_communities.role_coord_admin").id),
            (4, self.env.ref("energy_communities.role_coord_worker").id),
        ]
        for record in self:
            if record.code == "role_platform_admin":
                record.priority = 1
                record.available_role_ids = []
            elif record.code == "role_coord_admin":
                record.priority = 2
                record.available_role_ids = available_roles
            elif record.code == "role_ce_admin":
                record.priority = 3
                record.available_role_ids = available_roles
            elif record.code == "role_ce_manager":
                record.priority = 4
                record.available_role_ids = available_roles
            elif record.code == "role_ce_member":
                record.priority = 5
                record.available_role_ids = available_roles
            elif record.code == "role_coord_worker":
                record.priority = 6
                record.available_role_ids = available_roles
            elif record.code == "role_internal_user":
                record.priority = 7
                record.available_role_ids = available_roles + internal_user_extra_roles


class ResUsersRoleLine(models.Model):
    _inherit = "res.users.role.line"

    _sql_constraints = [
        (
            "user_role_uniq",
            "unique (user_id,role_id,company_id)",
            "Roles can be assigned to a user only once at a time",
        )
    ]

    code = fields.Char(related="role_id.code")
