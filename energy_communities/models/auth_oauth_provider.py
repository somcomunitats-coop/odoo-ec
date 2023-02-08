from odoo import fields, models, api


class OAuthProvider(models.Model):
    _inherit = 'auth.oauth.provider'

    is_admin_provider = fields.Boolean(string="Admin provider")
    superuser = fields.Char(string='Superuser', help='A super power user that is able to CRUD users on KC.',
                            placeholder='admin', required=False)
    superuser_pwd = fields.Char(string='Superuser password', help='"Superuser" user password',
                                placeholder='I hope is not "admin"', required=False)
    admin_user_endpoint = fields.Char(string='User admin URL', required=True,
                                      default='http://10.0.3.1:8080/admin/realms/REALM/users')
    root_endpoint = fields.Char(string='Root URL', required=True,
                                      default='http://10.0.3.1:8080/')
    realm_name = fields.Char(string='Realm name', required=True, default='0')
