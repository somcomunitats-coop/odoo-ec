from odoo import _, fields, models


class ResUsersRole(models.Model):
    _inherit = "res.users.role"

    SPECIFIC_LAYER = "specific_functional_layer"
    COMMON_LAYER = "common_functional_layer"

    APPLICATION_SCOPE_CHOICES = [
        (SPECIFIC_LAYER, _("Specific layer")),
        (COMMON_LAYER, _("Common layer")),
    ]

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

    application_scope = fields.Selection(
        selection=APPLICATION_SCOPE_CHOICES,
        string=_("Application scope"),
        compute="_compute_priority_and_available_roles",
    )

    # TODO: Try to refactor this to integrate better with energy_communities_api (method overwrite there)
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
        ]
        for record in self:
            if record.code == "role_platform_admin":
                record.priority = 1
                record.available_role_ids = []
                record.application_scope = self.SPECIFIC_LAYER
            elif record.code == "role_coord_admin":
                record.priority = 2
                record.available_role_ids = available_roles
                record.application_scope = self.SPECIFIC_LAYER
            elif record.code == "role_ce_manager":
                record.priority = 3
                record.available_role_ids = available_roles
                record.application_scope = self.SPECIFIC_LAYER
            elif record.code == "role_ce_admin":
                record.priority = 4
                record.available_role_ids = available_roles
                record.application_scope = self.SPECIFIC_LAYER
            elif record.code == "role_ce_member":
                record.priority = 5
                record.available_role_ids = available_roles
                record.application_scope = self.SPECIFIC_LAYER
            elif record.code == "role_internal_user":
                record.priority = 6
                record.available_role_ids = available_roles + internal_user_extra_roles
                record.application_scope = self.COMMON_LAYER
            elif record.code == "role_api_provider":
                record.priority = 7
                record.available_role_ids = []
                record.application_scope = self.SPECIFIC_LAYER


class ResUsersRoleLine(models.Model):
    _inherit = "res.users.role.line"

    _sql_constraints = [
        (
            "user_role_uniq",
            "unique(user_id,role_id,company_id)",
            "Roles can be assigned to a user only once at a time",
        )
    ]

    code = fields.Char(related="role_id.code")
