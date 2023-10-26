from odoo import fields, models


class ResUsersRole(models.Model):
    _inherit = "res.users.role"

    code = fields.Char(string="Code")


class ResUsersRoleLine(models.Model):
    _inherit = "res.users.role.line"
