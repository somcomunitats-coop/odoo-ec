from odoo import models, fields


class ResUsersRole(models.Model):
    _inherit = 'res.users.role'

    code = fields.Char(string='Code')
