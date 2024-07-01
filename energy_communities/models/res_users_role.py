from odoo import fields, models


class ResUsersRole(models.Model):
    _inherit = "res.users.role"

    code = fields.Char(string="Code")
    priority = fields.Integer(string="Priority")
    available_role_ids = fields.Many2many('res.users.role', 'res_users_role_rel',
                                          'rol_id', 'available_role_id',
                                          string='Available roles')


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
