from odoo import _, fields, models


class ResUsersRole(models.Model):
    _inherit = "res.users.role"

    code = fields.Char(string="Code")
    priority = fields.Integer(string=_("Priority"))


class ResUsersRoleLine(models.Model):
    _inherit = "res.users.role.line"

    code = fields.Char(related="role_id.code")
