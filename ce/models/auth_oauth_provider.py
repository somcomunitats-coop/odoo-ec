from odoo import fields, models, api

class OAuthProvider(models.Model):
    _inherit = 'auth.oauth.provider'

    company_id = fields.Many2one(
        string='Companyia',
        comodel_name='res.company',
    )
    
    login_provider = fields.Boolean(string='For users login')

    @api.model
    def update_ce_oauth_providers(self,kc_url,kc_port):
        if any([kc_url,kc_port]):
            pass #todo: update the existing providers related to the ce module accordingly

            
        

