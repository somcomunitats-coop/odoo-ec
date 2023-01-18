from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging
logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    USER_CE_ROLE_NAMES_SELECTION = [
        ('role_ce_member',_('CE Member')),
        ('role_ce_admin',_('CE Administrator')),
        ('role_platform_admin',_('Platform Administrator'))]

    ce_role = fields.Selection(USER_CE_ROLE_NAMES_SELECTION, string='CE Role', compute='_compute_ce_role')

    @api.depends('role_ids')
    def _compute_ce_role(self):

        role_ce_member_id = self.env['ir.model.data'].get_object_reference('ce','role_ce_member')[1]
        role_ce_admin_id = self.env['ir.model.data'].get_object_reference('ce','role_ce_admin')[1]
        role_platform_admin_id =  self.env['ir.model.data'].get_object_reference('ce','role_platform_admin')[1]

        for user in self:
            ce_role_ids = [r.id for r in user.role_ids if r.id in [role_ce_member_id, role_ce_admin_id, role_platform_admin_id]]

            role_value=None

            if role_platform_admin_id in ce_role_ids:
                role_value = 'role_platform_admin'
            elif role_ce_admin_id in ce_role_ids:
                role_value = 'role_ce_admin'
            elif role_ce_member_id in ce_role_ids:
                role_value = 'role_ce_member'

            user.ce_role = role_value

    @api.model
    def ce_user_roles_mapping(self):

        ICPSudo = self.env['ir.config_parameter'].sudo()

        roles_map = {
            'role_ce_member':
                {'odoo_role_id': int(ICPSudo.get_param('ce.odoo_group_ce_member')),
                'kc_group_name': ICPSudo.get_param('ce.ck_user_group_mapped_to_odoo_group_ce_member'),
                'kc_role_name': ICPSudo.get_param('ce.ck_role_mapped_to_odoo_group_ce_member'),
                'is_admin': False},
            'role_ce_admin':
                {'odoo_role_id': int(ICPSudo.get_param('ce.odoo_group_ce_admin')),
                'kc_group_name': ICPSudo.get_param('ce.ck_user_group_mapped_to_odoo_group_ce_admin'),
                'kc_role_name': ICPSudo.get_param('ce.ck_role_mapped_to_odoo_group_ce_admin'),
                'is_admin': True},
            'role_platform_admin':
                {'odoo_role_id': int(ICPSudo.get_param('ce.odoo_group_platform_admin')),
                'kc_group_name': ICPSudo.get_param('ce.ck_user_group_mapped_to_odoo_group_platform_admin'),
                'kc_role_name': ICPSudo.get_param('ce.ck_role_mapped_to_odoo_group_platform_admin'),
                'is_admin': True}
            }

        return roles_map
