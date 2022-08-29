from email.policy import default
from odoo import api, models, fields, _
import re

class ResCompany(models.Model):
    _inherit = 'res.company'

    # when OVor WP are doing API calls to Odoo will use odoo_cempany_id = -1 in order to refer to the 'Coordinadora' one
    API_PARAM_ID_VALUE_FOR_COORDINADORA = -1

    # overrided fields
    vat = fields.Char(related='partner_id.vat', string="Tax ID", readonly=False, required=True)
    # new fields
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

    cooperator_journal = fields.Many2one(
        "account.journal",
        string="Cooperator Journal",
        domain="[('type','=','sale'),('active','=',True)]",
        help="This journal will be"
        " the default one as the"
        " receivable journal for the"
        " cooperators"
    )

    @api.model
    def get_real_ce_company_id(self, api_param_odoo_compant_id):
        if api_param_odoo_compant_id == self.API_PARAM_ID_VALUE_FOR_COORDINADORA:
            return self.search([('coordinator','=',True)],limit=1) or None
        else:
            return self.search([('id','=',api_param_odoo_compant_id)]) or None


    @api.multi
    def get_ce_members(self, domain_key='in_kc_and_active'):
        domains_dict = {'in_kc_and_active': [('company_id','=',self.id),('oauth_uid','!=',None),('active','=',True)]}
        members = self.env['res.users'].sudo().search(domains_dict['in_kc_and_active'])
        return members
