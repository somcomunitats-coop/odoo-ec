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

        # [1] Set res.config.settings params that are company dependants

        # TODO choose the proper one depending of the legaol type of the new company
        pyme_char_template_id =  self.env['ir.model.data'].get_object_reference('l10n_es', 'account_chart_template_pymes')[1]
        #assoc_char_template_id =  self.env['ir.model.data'].get_object_reference('l10n_es', 'account_chart_template_assoc')[1]

        user_active_company_id = self.env.user.company_id.id
        user = self.env.user
        user.company_ids = [(4,self.id)]
        user.company_id = self.id
        rcs_sudo = self.env['res.config.settings'].sudo(user)
        rcs_sudo_id = rcs_sudo.create({
            'chart_template_id': pyme_char_template_id,
            'kc_realm': str(self.id),
            })
        rcs_sudo_id.execute()

        # [2] Create new Sequences and Subscription Journal
        #default_subs_acc_jour_seq = self.env.ref('easy_my_coop.sequence_subscription_journal')
        subs_acc_jour_seq = self.env['ir.sequence'].sudo(user).create({
            'name': 'Account Subscription Journal Sequence',
            'padding': 3,
            'prefix': 'SUBJ/%(year)s/',
            'use_date_range': True,
            'number next': 1,
            'number_increment': 1,
            'company_id': self.id,
        })

        subs_acc_jour = self.env['account.journal'].sudo(user).create({
            'name': 'Account Subscription Journal',
            'invoice_sequence_id': subs_acc_jour_seq.id,
            'type': 'sale',
            'code': 'SUB_',
            'sequence_number next': 1,
            'company_id': self.id,
            })

        self.sudo(user).cooperator_journal = subs_acc_jour.id

        # [3] update several accounts
        xml_id_4400 = "{}_{}".format(self.id, 'account_common_4400') # 440000 | Deudores (euros)
        account_4400_id = self.env['ir.model.data'].get_object_reference('l10n_es', xml_id_4400)[1]
        self.sudo(user).property_cooperator_account = account_4400_id

        xml_id_7000 = "{}_{}".format(self.id, 'account_common_7000') # 700000 | Ventas de mercaderías en España
        account_7000_id = self.env['ir.model.data'].get_object_reference('l10n_es', xml_id_7000)[1]
        self.env.ref('easy_my_coop.product_category_company_share').sudo(user).property_account_income_categ_id = account_7000_id

        xml_id_600 = "{}_{}".format(self.id, 'account_common_600') # 600000 | Ventas de mercaderías en España
        account_600_id = self.env['ir.model.data'].get_object_reference('l10n_es', xml_id_600)[1]
        self.env.ref('easy_my_coop.product_category_company_share').sudo(user).property_account_expense_categ_id = account_600_id

        # RECOVER THE ORIGINAL ACTIVE COMPANY_ID TO CURRENT USER
        user.company_id = user_active_company_id

    @api.multi
    def _create_keycloak_realm(self):
        self.ensure_one()
        pass

    @api.multi
    def _community_post_keycloak_creation_tasks(self):
        """ Do post Kaykoac Realm creation tasks"""
        self.ensure_one()
        pass
