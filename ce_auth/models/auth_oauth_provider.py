from odoo import fields, models, api


class OAuthProvider(models.Model):
    _inherit = 'auth.oauth.provider'

    superuser = fields.Char(
        help='A super power user that is able to CRUD users on KC.',
        placeholder='admin',
        required=False,
    )
    superuser_pwd = fields.Char(
        help='"Superuser" user password',
        placeholder='I hope is not "admin"',
        required=False,
    )
