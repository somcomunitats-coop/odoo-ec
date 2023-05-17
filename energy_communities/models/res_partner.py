from odoo import api, fields, models, SUPERUSER_ID
import logging

logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    gender = fields.Selection(selection_add=[("not_binary", "Not binary"),
                                             ("not_share", "I prefer to not share it")])

    user_is_ce_member = fields.Boolean(string='Current user is CE member', compute='_user_is_ce_member')
    user_is_platform_admin = fields.Boolean(string='Current user is Platform admin', compute='_user_is_platform_admin')

    def _user_is_ce_member(self):
        for record in self:
            user = self.env.user
            is_ce_member = user.role_ids.code == 'role_ce_admin'
            record.user_is_ce_member = is_ce_member

    def _user_is_platform_admin(self):
        for record in self:
            user = self.env.user
            is_platform_admin = user.role_ids.code == 'role_platform_admin'
            record.user_is_platform_admin = is_platform_admin

    @api.model
    def create(self, vals):
        current_company = self.env.company
        if current_company.hierarchy_level != 'instance':
            if vals.get('company_ids', False):
                vals['company_ids'][0][-1].append(current_company.id)

        new_parner = super(ResPartner, self).create(vals)
        return new_parner

    def cron_update_company_ids_from_user(self):
        partner_with_users = self.search([('user_ids', '!=', False), ('user_ids.id', '!=', SUPERUSER_ID)])
        for partner in partner_with_users:
            logger.info("Updated company_ids to partner {}".format(partner.display_name))
            if partner.user_ids.company_ids.ids:
                partner.write({
                    'company_ids': partner.user_ids.company_ids.ids
                })
        self.env['res.users'].browse(SUPERUSER_ID).partner_id.write({
            'company_ids': False
        })

    def get_cooperator_from_vat(self, vat):
        if vat:
            vat = vat.strip()
        # email could be falsy or be only made of whitespace.
        if not vat:
            return self.browse()
        partner = self.search(
            [("vat", "ilike", vat)], limit=1
        )
        return partner
