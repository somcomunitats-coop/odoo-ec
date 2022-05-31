from odoo import fields, models, api

class OAuthProvider(models.Model):
    _inherit = 'auth.oauth.provider'

    company_id = fields.Many2one(
        string='Companyia',
        comodel_name='res.company',
    )
    login_provider = fields.Boolean(string='For users login')
