from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging
logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    USER_CE_ROLES = [('role_ce_member',_('CE Member')),('role_ce_admin',_('CE Administrator')),('role_platform_admin',_('Platform Administrator'))]

    ce_role = fields.Selection(USER_CE_ROLES, string='CE Role', compute='_compute_ce_role')

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

    @api.multi
    def push_new_user_to_keyckoack(self):
        self.ensure_one()

        ICPSudo = self.env['ir.config_parameter'].sudo()
        ce_admin_provider = self.company_id.ce_admin_key_cloak_provider_id
        ce_login_provider = self.company_id.auth_ce_key_cloak_provider_id

        if not ce_admin_provider:
            raise UserError(
                _("Unable to get the 'CE admin' provider_id related to tha current company when triying to push new user to KC."))

        wiz_vals = {
            'provider_id': ce_admin_provider.id,
            'user_ids': [(6, 0, [self.id])],
            'endpoint': ce_admin_provider.users_endpoint,
            'user': ce_admin_provider.superuser,
            'pwd': ce_admin_provider.superuser_pwd,
            'login_match_key': 'username:login'
        }

        ck_user_group_mapped_to_odoo_group_ce_member = ICPSudo.get_param(
            'ce.ck_user_group_mapped_to_odoo_group_ce_member')
        kc_user_additional_vals = {
            'attributes': {'lang': [self.lang]},
            'groups': [ck_user_group_mapped_to_odoo_group_ce_member],
            'enabled': True,
            'credentials': [
                {'type': 'password', 'value': 'w8P=FL_W', 'temporary': False}],
        }
        self = self.with_context(kc_user_creation_vals=kc_user_additional_vals)
        wiz = self.env['auth.keycloak.create.wiz'].create(wiz_vals)
        wiz.button_create_user()

        # after call the button_create_user() we need to re-set the user.oauth_provider_id
        # in order to ensure that it remains = ce_login_provider
        self.update({
            'oauth_provider_id': ce_login_provider,
        })

    @api.multi
    def update_user_data_to_keyckoack(self, kc_data_to_update=[]):
        """Proceed to update the related Keyckoak data for current user (=Self)

        :param kc_data_to_update: <list of strings> list of KeyCloak user data to update.
            If empty list proceed to update all the KC allowed updatable fields (see list: _KEYCLOAK_UPDATABLE_USER_DATA)
        """
        self.ensure_one()
        ce_admin_provider = self.company_id.ce_admin_key_cloak_provider_id

        if not ce_admin_provider:
            raise UserError(
                _("Unable to get the 'CE admin' provider_id related to tha current company when triying to push new user to KC."))

        if not self.oauth_uid:
            raise UserError(
                _("The Odoo user %s (Odoo id: %s)do not have any mapped Keycloak Ured ID."%(self.id, self.login)))

        wiz_vals = {
            'provider_id': ce_admin_provider.id,
            'endpoint': ce_admin_provider.users_endpoint,
            'user': ce_admin_provider.superuser,
            'pwd': ce_admin_provider.superuser_pwd,
            'login_match_key': 'username:login'
        }
        kc_wiz = self.env['auth.keycloak.sync.wiz'].create(wiz_vals)
        kc_wiz._validate_setup()

        token = kc_wiz._get_token()

        to_up_data_dict = kc_wiz._update_user_values(self, kc_data_to_update)
        resp = kc_wiz._update_user_by_id(token, self.oauth_uid, to_up_data_dict)

        return resp

    @api.multi
    def ce_user_roles_mapping(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ce_member_key = ICPSudo.get_param('ce.ck_user_group_mapped_to_odoo_group_ce_member')
        ce_member_role_value = int(ICPSudo.get_param('ce.odoo_group_ce_member'))

        ce_admin_key = ICPSudo.get_param('ce.ck_user_group_mapped_to_odoo_group_ce_admin')
        ce_admin_role_value = int(ICPSudo.get_param('ce.odoo_group_ce_admin'))

        platform_admin_key = ICPSudo.get_param('ce.ck_user_group_mapped_to_odoo_group_platform_admin')
        platform_admin_role_value = int(ICPSudo.get_param('ce.odoo_group_platform_admin'))

        roles_map = { ce_member_key: ce_member_role_value,
                       ce_admin_key: ce_admin_role_value,
                       platform_admin_key: platform_admin_role_value}
        return roles_map

