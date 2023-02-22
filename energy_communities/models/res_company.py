from email.policy import default
from sqlite3 import dbapi2
from odoo import api, models, fields, _
from datetime import datetime
import re
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    coordinator = fields.Boolean(string='Platform coordinator',
                                 help="Flag to indicate that this company has the rol of 'Coordinator'(=Administrator) for the current 'Comunitats Energètiques' Platform"
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
        'Initial Subscription Share Amount', digits='Product Price')
    allow_new_members = fields.Boolean(
        string="Allow new members", default=True)
    create_user_in_keycloak = fields.Boolean('Create user for keycloak',
                                             help='Users created by cooperator are pushed automatically to keycloak',
                                             default=False)

    @api.model
    def get_real_ce_company_id(self, api_param_odoo_compant_id):
        if api_param_odoo_compant_id == self.API_PARAM_ID_VALUE_FOR_COORDINADORA:
            return self.search([('coordinator', '=', True)], limit=1) or None
        else:
            return self.search([('id', '=', api_param_odoo_compant_id)]) or None

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
            #sanit_name = slugify(vals['name'])
            sanit_name = vals['name']
            #if sanit_name in [slugify(c.name) for c in self.search([]) if c.name]:
            if sanit_name in [c.name for c in self.search([]) if c.name]:
                raise UserError(
                    _("Unable to create new company because there is an allready existing company with this NAME: {}").format(vals['name']))

    @api.model
    def create(self, vals):

        # check that we are not creating duplicate companies by vat or by name
        self._is_not_unique(vals)

        new_company = super(ResCompany, self).create(vals)

        return new_company

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
