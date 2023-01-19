from email.policy import default
from sqlite3 import dbapi2
from odoo import api, models, fields, _
from datetime import datetime
import re
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as OAL
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

    foundation_date = fields.Date('Foundation date')
    social_telegram = fields.Char('Telegram Account')
    initial_subscription_share_amount = fields.Float(
        'Initial Subscription Share Amount', digits=dp.get_precision('Product Price'))
    allow_new_members = fields.Boolean(
        string="Allow new members", default=True)

    @api.model
    def get_real_ce_company_id(self, api_param_odoo_compant_id):
        if api_param_odoo_compant_id == self.API_PARAM_ID_VALUE_FOR_COORDINADORA:
            return self.search([('coordinator', '=', True)], limit=1) or None
        else:
            return self.search([('id', '=', api_param_odoo_compant_id)]) or None

    @api.multi
    def check_ce_has_admin(self):
        self.ensure_one()
        admin_roles_ids = [r['odoo_role_id']
                           for r in self.env['res.users'].ce_user_roles_mapping().values() if r['is_admin']]
        company_user_ids = self.get_ce_members().ids
        admins_user_ids = []
        for admin_role in self.env['res.users.role'].sudo().browse(admin_roles_ids):
            for role_line in admin_role.line_ids:
                admins_user_ids.append(role_line.user_id.id)
        return any([user in admins_user_ids for user in company_user_ids])

    @api.multi
    def get_ce_members(self, domain_key='in_kc_and_active'):
        domains_dict = {'in_kc_and_active': [
            ('company_id', '=', self.id), ('oauth_uid', '!=', None), ('active', '=', True)]}
        members = self.env['res.users'].sudo().search(
            domains_dict['in_kc_and_active'])
        return members

    @api.model
    def _is_not_unique(self, vals):

        # check for VAT
        if vals.get('vat', False) and vals.get('vat'):
            sanit_vat = re.sub(r"[^a-zA-Z0-9]", "", vals['vat']).lower()
            if sanit_vat in [re.sub(r"[^a-zA-Z0-9]", "", c.vat).lower() for c in self.search([]) if c.vat]:
                raise UserError(
                    _("Unable to create new company because there is an allready existing company with this VAT number: {}").format(vals['vat']))

        # check for name
        if vals.get('name', False) and vals.get('name'):
            sanit_name = slugify(vals['name'])
            if sanit_name in [slugify(c.name) for c in self.search([]) if c.name]:
                raise UserError(
                    _("Unable to create new company because there is an allready existing company with this NAME: {}").format(vals['name']))

    @api.model
    def create(self, vals):

        # check that we are not creating duplicate companies by vat or by name
        self._is_not_unique(vals)

        new_company = super(ResCompany, self).create(vals)

        return new_company

    @api.multi
    def _community_post_company_creation_tasks(self):
        """ Do post company creation tasks that are specific for the CCEE project"""
        self.ensure_one()

        # [1] Set res.config.settings params that are company dependants
        # TODO choose the proper one depending of the legaol type of the new company
        pyme_char_template_id = self.env['ir.model.data'].get_object_reference(
            'l10n_es', 'account_chart_template_pymes')[1]
        #assoc_char_template_id =  self.env['ir.model.data'].get_object_reference('l10n_es', 'account_chart_template_assoc')[1]

        user_active_company_id = self.env.user.company_id.id
        user = self.env.user
        user.company_ids = [(4, self.id)]
        user.company_id = self.id
        rcs_sudo = self.env['res.config.settings'].sudo(user)
        rcs_sudo_id = rcs_sudo.create({
            'chart_template_id': pyme_char_template_id,
            'kc_realm': str(self.id),
        })
        rcs_sudo_id.execute()
        user.company_id = user_active_company_id

        # [2] Create new Sequences and Subscription Journal
        subs_acc_jour_seq = self.env['ir.sequence'].sudo().create({
            'name': 'Account Subscription Journal Sequence',
            'padding': 3,
            'prefix': 'SUBJ/%(year)s/',
            'use_date_range': True,
            'number next': 1,
            'number_increment': 1,
            'company_id': self.id,
            'date_range_ids': [(0, 0, {
                'date_from': '{}-01-01'.format(datetime.now().year),
                'date_to': '{}-12-31'.format(datetime.now().year),
                'number_next': 1,
                'number_next_actual': 1})]
        })
        subs_acc_jour = self.env['account.journal'].sudo().create({
            'name': 'Account Subscription Journal',
            'invoice_sequence_id': subs_acc_jour_seq.id,
            'type': 'sale',
            'code': 'SUB_',
            'sequence_number next': 1,
            'company_id': self.id,
        })

        self.sudo().cooperator_journal = subs_acc_jour.id

        # [3] update several accounts
        # 440000 | Deudores (euros)
        xml_id_4400 = "{}_{}".format(self.id, 'account_common_4400')
        account_4400_id = self.env['ir.model.data'].sudo(
        ).get_object_reference('l10n_es', xml_id_4400)[1]

        self.sudo().property_cooperator_account = account_4400_id

        # 700000 | Ventas de mercaderías en España
        xml_id_7000 = "{}_{}".format(self.id, 'account_common_7000')
        account_7000_id = self.env['ir.model.data'].get_object_reference(
            'l10n_es', xml_id_7000)[1]
        self.env.ref('easy_my_coop.product_category_company_share').sudo(
        ).property_account_income_categ_id = account_7000_id

        # 600000 | Ventas de mercaderías en España
        xml_id_600 = "{}_{}".format(self.id, 'account_common_600')
        account_600_id = self.env['ir.model.data'].get_object_reference(
            'l10n_es', xml_id_600)[1]
        self.env.ref('easy_my_coop.product_category_company_share').sudo(
        ).property_account_expense_categ_id = account_600_id

        # [4] create default_share_product
        product_vals = {
            'name': 'Quota inicial alta sòcia',
            'short_name': 'Quota inicial alta sòcia',
            'sale_ok': True,
            'purchase_ok': False,
            'is_share': True,
            'display_on_website': True,
            'categ_id': self.env.ref('easy_my_coop.product_category_company_share').id,
            'type': 'service',
            'default_code': 'quota_inicial_alta_sòcia',
            'default_share_product': True,
            'list_price': self.initial_subscription_share_amount or 0.00,
            'customer': True,
            'by_company': True,
            'by_individual': True,
            'company_id': self.id,
        }
        self.env['product.template'].sudo().create(product_vals)

    @api.multi
    def _create_keycloak_entities(self):
        self.ensure_one()
        # 1) CREATE CE_ ADMIN PROVIDER:
        # todo: we assume that "unique platform realm" is allready created with KC name = '0'
        # todo: we assume that "unique odoo" client is allready created with client_id = 'odoo'
        # but we need to implement the creation of it just after module 'ce' installation
        platform_realm_name = '0'  # Platform unique KC ealm
        odoo_client_id = 'odoo' #Platform unique Odoo KC Client
        # get realm_admin provider
        # this provider will be a supra-company one (platform) related to the "UNIQUE" platform '0' realm
        # so it will not be necessary to create it here because it will already exist
        realm_0_admin_provider = self.env.ref('ce.default_platform_admin_keycloak_provider')
        self.ce_admin_key_cloak_provider_id = realm_0_admin_provider.id

        wiz_vals = {
            'provider_id': realm_0_admin_provider.id,
            'endpoint': realm_0_admin_provider.users_endpoint,
            'user': realm_0_admin_provider.superuser,
            'pwd': realm_0_admin_provider.superuser_pwd,
            'login_match_key': 'username:login'
        }
        realm_admin_wiz = self.env['auth.keycloak.sync.wiz'].sudo().create(wiz_vals)
        realm_admin_wiz._validate_setup()
        token = realm_admin_wiz._get_token()

        clients_repr_list = realm_admin_wiz._get_clients(token, odoo_client_id)

        if not clients_repr_list:
            raise UserError(
                _("Unable to get the 'secret key' related to the KC Odoo client: {}").format(odoo_client_id))

        odoo_client_secret = realm_admin_wiz._get_client_secret(token, clients_repr_list[0]['id'])
        ce_odoo_login_provider = self.env['auth.oauth.provider'].sudo().create({
            'name': '{} (login-CE)'.format(self.name),
            'body': '{} (login-CE)'.format(self.name),
            'client_id': odoo_client_id,
            'client_secret': odoo_client_secret,
            'login_provider': True,
            'company_id': self.id,
            'auth_endpoint': realm_0_admin_provider.auth_endpoint.replace('/master/','/{}/'.format(platform_realm_name)),
            'validation_endpoint': realm_0_admin_provider.validation_endpoint.replace('/master/','/{}/'.format(platform_realm_name)),
            'data_endpoint': realm_0_admin_provider.data_endpoint.replace('/master/','/{}/'.format(platform_realm_name)),
            'scope': 'openid',
            'enabled': True,
        })
        self.auth_ce_key_cloak_provider_id = ce_odoo_login_provider.id

    @api.multi
    def _community_post_keycloak_creation_tasks(self):
        """ Do post Kaykoac Realm creation tasks"""
        self.ensure_one()
        pass

    @api.multi
    def get_active_services(self):
        """Return a list of dicts with the key data of each active Service"""
        self.ensure_one()
        ret = []

        # TODO: in a further iteration it will get the data from the "community services model"
        # but nowadays (2022-09-26) it still don't exists so we are getting this info from the related crm_lead.tag_ids

        creation_ce_source_id = self.env['ir.model.data'].get_object_reference(
            'ce', 'ce_source_creation_ce_proposal')[1]
        coordinator_id = self.get_real_ce_company_id(
            self.API_PARAM_ID_VALUE_FOR_COORDINADORA).id

        lead_from = self.env['crm.lead'].sudo().search(
            [('company_id', '=', coordinator_id),
             ('community_company_id', '=', self.id),
             ('source_id', '=', creation_ce_source_id)], limit=1)

        if lead_from:
            for tag in lead_from.tag_ids:
                ret.append({
                    'id': tag.id,
                    'name': tag.name,
                })
        return ret

    @api.multi
    def get_public_web_landing_url(self):
        """Return the URL that points to the public landing web of the CE, reading it from the related
        map place (field: external_link_url)"""
        self.ensure_one()
        ret = []

        coordinator_id = self.get_real_ce_company_id(
            self.API_PARAM_ID_VALUE_FOR_COORDINADORA).id

        related_map_place = self.env['crm.team'].sudo().search(
            [('company_id', '=', coordinator_id),
             ('community_company_id', '=', self.id), ('map_id', '=', self.env.ref('ce.ce_default_cm_map').id)], limit=1)

        return related_map_place and related_map_place.external_link_url or None

    @api.multi
    def get_keycloak_odoo_login_url(self):
        self.ensure_one()
        provider_dict = [p_dict for p_dict in OAL().list_providers() if p_dict.get('id') and p_dict.get('id') == self.auth_ce_key_cloak_provider_id.id]
        return provider_dict and provider_dict[0] and provider_dict[0]['auth_link'] or ''

    @api.multi
    def get_kc_groups_data(self):
        """Proceed to get the list of the KC groups related to the current company > Realm"""
        self.ensure_one()
        ce_admin_provider = self.ce_admin_key_cloak_provider_id

        if not ce_admin_provider:
            raise UserError(
                _("Unable to get the 'CE admin' provider_id related to tha current company when triying to push new user to KC."))

        wiz_vals = {
            'provider_id': ce_admin_provider.id,
            'endpoint': ce_admin_provider.users_endpoint,
            'user': ce_admin_provider.superuser,
            'pwd': ce_admin_provider.superuser_pwd,
            'login_match_key': 'username:login'
        }
        kc_wizard = self.env['auth.keycloak.sync.wiz'].create(wiz_vals)
        kc_wizard._validate_setup()
        token = kc_wizard._get_token()

        return kc_wizard._get_realm_groups_data(token)
