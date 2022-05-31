from odoo import api, models, fields, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    coordinator = fields.Boolean(string='Platform coordinator', 
        help="Flag to indicate that this company has the rol of 'Coordinator'(=Administrator) for the current 'Comunitats Energètiques' Platform"
        )
    
    platform_admin_key_cloak_provider_id = fields.Many2one(        
        string='OAuth provider for Platform admin',
        comodel_name='auth.oauth.provider', 
    )
    ce_admin_key_cloak_provider_id = fields.Many2one(        
        string='OAuth provider for CCEE admin',
        comodel_name='auth.oauth.provider',
    )
    auth_ce_key_cloak_provider_id = fields.Many2one(        
        string='OAuth provider for CCEE login',
        comodel_name='auth.oauth.provider',
    )