from odoo import models, fields


CE_ADMIN_ROLE = 'role_ce_admin'
PLATFORM_ADMIN_ROLE = 'role_platform_admin'
CE_MEMBER_ROLE = 'role_ce_member'


class ResUsersRole(models.Model):
    _inherit = 'res.users.role'

    code = fields.Char(string='Code')
