from email.policy import default
from odoo import api, models, fields, _
import re
from odoo.exceptions import UserError
from slugify import slugify

class ResCompany(models.Model):
    _inherit = 'res.company'

    # when OVor WP are doing API calls to Odoo will use odoo_cempany_id = -1 in order to refer to the 'Coordinadora' one
    API_PARAM_ID_VALUE_FOR_COORDINADORA = -1

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

    @api.model
    def check_ce_has_admin(self):
        ce_roles_map = self.env['res.users'].sudo().ce_user_roles_mapping()
        ce_admin_key = self.env['ir.config_parameter'].sudo().get_param('ce.ck_user_group_mapped_to_odoo_group_ce_admin')
        company_user_ids = self.env['res.users'].search([('company_id', '=', self.id)]).ids
        admin_ids = self.env['res.users.role'].browse(ce_roles_map[ce_admin_key]).user_ids.ids
        return any([user in admin_ids for user in company_user_ids])

    @api.multi
    def get_ce_members(self, domain_key='in_kc_and_active'):
        domains_dict = {'in_kc_and_active': [('company_id','=',self.id),('oauth_uid','!=',None),('active','=',True)]}
        members = self.env['res.users'].sudo().search(domains_dict['in_kc_and_active'])
        return members

    @api.model
    def _is_not_unique(self, vals):

        # check for VAT
        if vals.get('vat', False) and vals.get('vat'):
            sanit_vat = re.sub(r"[^a-zA-Z0-9]","",vals['vat']).lower()
            if sanit_vat in [re.sub(r"[^a-zA-Z0-9]","",c.vat).lower() for c in self.search([]) if c.vat]:
                raise UserError(
                    _("Unable to create new company because there is an allready existing company with this VAT number: {}").format(vals['vat']))

        # check for name
        if vals.get('name', False) and vals.get('name'):
            sanit_name = slugify(vals['name'])
            if sanit_name in [slugify(c.name) for c in self.search([]) if c.name]:
                raise UserError(
                    _("Unable to create new company because there is an allready existing company with this NAME: {}").format(vals['name']))


    @api.model
    def create(self,vals):

        # check that we are not creating duplicate companies by vat or by name
        self._is_not_unique(vals)

        new_company = super(ResCompany,self).create(vals)

        return new_company

    @api.multi
    def _community_post_company_creation_tasks(self):
        """ Do post company creation tasks that are specific for the CCEE project"""
        self.ensure_one()
        pass

    @api.multi
    def _create_keycloak_realm(self):
        self.ensure_one()
        pass

    @api.multi
    def _community_post_keycloak_creation_tasks(self):
        """ Do post Kaykoac Realm creation tasks"""
        self.ensure_one()
        pass



    
