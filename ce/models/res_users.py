from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging
logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def push_new_user_to_keyckoack(self):
        self.ensure_one()

        ICPSudo = self.env['ir.config_parameter'].sudo()
        ce_admin_provider = self.company_id.ce_admin_key_cloak_provider_id
        ce_login_provider = self.company_id.auth_ce_key_cloak_provider_id

        if not ce_admin_provider:
            raise UserError(_("Unable to get the 'CE admin' provider_id related to tha current company when triying to push new user to KC."))

        wiz_vals = {
            'provider_id': ce_admin_provider.id,
            'user_ids': [(6, 0, [self.id])],
            'endpoint': ce_admin_provider.users_endpoint,
            'user': ce_admin_provider.superuser,
            'pwd': ce_admin_provider.superuser_pwd, 
            'login_match_key': 'username:login'
        }

        ck_user_group_mapped_to_odoo_group_ce_member = ICPSudo.get_param('ce.ck_user_group_mapped_to_odoo_group_ce_member')
        kc_user_additional_vals = {
            'attributes':{'lang':[self.lang]},
            'groups': [ck_user_group_mapped_to_odoo_group_ce_member],
            'enabled': True,
            'credentials':[
                {'type':'password','value':'w8P=FL_W','temporary':False}],
        }
        self = self.with_context(kc_user_creation_vals=kc_user_additional_vals)
        wiz = self.env['auth.keycloak.create.wiz'].create(wiz_vals)
        wiz.button_create_user()

        # after call the button_create_user() we need to re-set the user.oauth_provider_id 
        # in order to ensure that it remains = ce_login_provider
        self.update({
            'oauth_provider_id': ce_login_provider,
        })
