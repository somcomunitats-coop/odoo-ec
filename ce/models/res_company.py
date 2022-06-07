from odoo import api, models, fields, _
import re

class ResCompany(models.Model):
    _inherit = 'res.company'

    #def _get_default_kc_realm_name(self):
    #    return ((self.vat and re.sub(r"[^a-zA-Z0-9]","",self.vat).lower()) or
    #        (self.name and re.sub(' +','_',re.sub(r"[^a-zA-Z0-9 ]","",self.name)).lower()))

    kc_realm = fields.Char(string='KeyCloak realm name')

    coordinator = fields.Boolean(string='Platform coordinator', 
        help="Flag to indicate that this company has the rol of 'Coordinator'(=Administrator) for the current 'Comunitats Energètiques' Platform"
        )
    
    ce_admin_key_cloak_provider_id = fields.Many2one(        
        string='OAuth provider for CCEE admin',
        comodel_name='auth.oauth.provider',
    )
    auth_ce_key_cloak_provider_id = fields.Many2one(        
        string='OAuth provider for CCEE login',
        comodel_name='auth.oauth.provider',
    )