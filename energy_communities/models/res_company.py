from email.policy import default
from sqlite3 import dbapi2
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime
import re
from odoo.exceptions import UserError

_HIERARCHY_LEVEL_VALUES = [
    ('instance', _('Instance')),
    ('coordinator', _('Coordinator')),
    ('community', _('Community'))
]


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.onchange('hierarchy_level')
    def onchange_hierarchy_level(self):
        self.parent_id = False

    @api.depends('hierarchy_level')
    def _compute_parent_id_filtered_ids(self):
        for rec in self:
            if rec.hierarchy_level == 'instance':
                rec.parent_id_filtered_ids = False
            elif rec.hierarchy_level == 'coordinator':
                rec.parent_id_filtered_ids = self.search([('hierarchy_level', '=', 'instance')])
            elif rec.hierarchy_level == 'community':
                rec.parent_id_filtered_ids = self.search([('hierarchy_level', '=', 'coordinator')])

    hierarchy_level = fields.Selection(selection=_HIERARCHY_LEVEL_VALUES, required=True, string="Hierarchy level",
                                       default='community')
    parent_id_filtered_ids = fields.One2many('res.company', compute=_compute_parent_id_filtered_ids, readonly=True,
                                             store=False)
    ce_tag_ids = fields.Many2many('crm.tag', string='Energy Community Services')
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
    voluntary_share_id = fields.Many2one(comodel_name='product.template', domain=[('is_share', '=', True)],
                                         string='Voluntary share to show on website')

    @api.constrains('hierarchy_level', 'parent_id')
    def _check_hierarchy_level(self):
        for rec in self:
            if rec.hierarchy_level == 'instance':
                if self.search_count([('hierarchy_level', '=', 'instance'), ('id', '!=', rec.id)]):
                    raise ValidationError(_('An instance company already exists'))
                if rec.parent_id:
                    raise ValidationError(_('You cannot create a instance company with a parent company.'))
            if rec.hierarchy_level == 'coordinator' and rec.parent_id.hierarchy_level != 'instance':
                raise ValidationError(_('Parent company must be instance hierarchy level.'))
            if rec.hierarchy_level == 'community' and rec.parent_id.hierarchy_level != 'coordinator':
                raise ValidationError(_('Parent company must be coordinator hierarchy level.'))

    @api.constrains('hierarchy_level', 'parent_id')
    def _check_hierarchy_level(self):
        for rec in self:
            if rec.hierarchy_level == 'instance':
                if self.search_count([('hierarchy_level', '=', 'instance'), ('id', '!=', rec.id)]):
                    raise ValidationError(_('An instance company already exists'))
                if rec.parent_id:
                    raise ValidationError(_('You cannot create a instance company with a parent company.'))
            if rec.hierarchy_level == 'coordinator' and rec.parent_id.hierarchy_level != 'instance':
                    raise ValidationError(_('Parent company must be instance hierarchy level.'))
            if rec.hierarchy_level == 'community' and rec.parent_id.hierarchy_level != 'coordinator':
                    raise ValidationError(_('Parent company must be coordinator hierarchy level.'))

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
                    _("Unable to create new company because there is an allready existing company with this VAT number: {}").format(
                        vals['vat']))

        # check for name
        if vals.get('name', False) and vals.get('name'):
            # sanit_name = slugify(vals['name'])
            sanit_name = vals['name']
            # if sanit_name in [slugify(c.name) for c in self.search([]) if c.name]:
            if sanit_name in [c.name for c in self.search([]) if c.name]:
                raise UserError(
                    _("Unable to create new company because there is an allready existing company with this NAME: {}").format(
                        vals['name']))

    @api.model
    def create(self, vals):

        # check that we are not creating duplicate companies by vat or by name
        self._is_not_unique(vals)

        new_company = super(ResCompany, self).create(vals)

        return new_company

    def get_active_services(self):
        """Return a list of dicts with the key data of each active Service"""
        self.ensure_one()
        res = []
        for tag in self.ce_tag_ids:
            res.append({
                'id': tag.id,
                'name': tag.name,
            })
        return res

    def get_public_web_landing_url(self):
        # TODO Get from community_maps
        return 'https://somcomunitats.coop/ce/comunitat-energetica-prova/'

    def get_keycloak_odoo_login_url(self):
        login_provider_id = self.env.ref('energy_communities.keycloak_login_provider')
        return login_provider_id.get_auth_link()
