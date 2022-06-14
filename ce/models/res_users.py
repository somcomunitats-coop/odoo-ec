from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging
logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def push_new_user_to_keyckoack(self):
        self.ensure_one()

        ce_admin_provider = self.company_id.ce_admin_key_cloak_provider_id

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
        wiz = self.env['auth.keycloak.create.wiz'].create(wiz_vals)
        wiz.button_create_user()
