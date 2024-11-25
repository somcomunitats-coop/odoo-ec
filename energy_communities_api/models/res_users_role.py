from odoo import fields, models


class ResUsersRole(models.Model):
    _inherit = "res.users.role"

    def _compute_priority_and_available_roles(self):
        super()._compute_priority_and_available_roles()
        api_roles = [
            (4, self.env.ref("energy_communities_api.role_api_provider").id),
        ]
        for record in self:
            if record.code == "role_api_provider":
                record.available_role_ids = api_roles
