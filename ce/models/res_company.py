from email.policy import default
from odoo import api, models, fields, _
import re

class ResCompany(models.Model):
    _inherit = 'res.company'

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
    def create(self,vals):
        company = super(ResCompany, self).create(vals)
        if company.id > 1:
            pass
            #todo's:
            # crear, per la nova companyia els registres que el òdul de easy_my_coop crea aquí
            # /odoo/addons/easy_my_coop/data/easy_my_coop_data.xml via xml per a la companyia 1 (='Coordinadora)
            # en el moment de instal·lar el mòdul, per exemple:
            # - la sequència numèrica de factures de quotes
            # - el diari de facturació de quotes
            # - el tipus bàsic de quota d'alta de sòcia (Share Type)

        return company