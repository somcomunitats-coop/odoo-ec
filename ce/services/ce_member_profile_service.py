import logging, json
from odoo.http import Response
from odoo.addons.base_rest.http import wrapJsonException
from odoo.addons.component.core import Component
from odoo import _
from . import schemas

_logger = logging.getLogger(__name__)


class MemberProfileService(Component):
    _inherit = "base.rest.private_abstract_service"
    _name = "ce.member.profile.services"
    _collection = "ce.services"
    _usage = "member-profile"
    _description = """
        CE Member profile requests
    """

    def get(self, **params):
        domain = self._prepare_get(params)
        user = self.env["res.users"].sudo().search(domain)
        if not user:  
            return Response(
                json.dumps({'message': _("No Odoo User found for KeyCloak user id %s") % id}),
                status=404,
                content_type="application/json")
   
        partner = user.partner_id or None
        if not partner:
            return Response(
                json.dumps({'message': _("No Odoo Partner found for Odoo user with login username %s") % user.login}),
                status=404,
                content_type="application/json")
          
        partner_bank = self.env['res.partner.bank'].sudo().search([
                ('partner_id', '=', partner.id), ('company_id', '=', partner.company_id.id)
            ], order="sequence asc", limit=1)

        sepa_mandate = partner_bank and any([sm.id for sm in partner_bank.mandate_ids if sm.state == 'valid']) or False

        # info_general = self.env['ir.model.data'].xmlid_to_object('ce.ce_source_general_info')
        # info_future_ce_by_zone = self.env['ir.model.data'].xmlid_to_object('ce.ce_source_future_location_ce_info')
        info_existing_ce_source = self.env['ir.model.data'].xmlid_to_object('ce.ce_source_existing_ce_info')

        news_subscription = any(self.env['crm.lead'].sudo().search([
                ('email_from', '=', partner.email), 
                ('source_id','=',info_existing_ce_source.id),
                ('company_id', '=', partner.company_id.id)
            ], order='id desc', limit=1))

        return self._to_dict(user, partner, partner_bank, sepa_mandate, news_subscription)

    def _validator_get(self):
        return schemas.S_CE_MEMBER_PROFILE_GET

    def _validator_return_get(self):
        return schemas.S_CE_MEMBER_PROFILE_RETURN_GET

    @staticmethod
    def _to_dict(user, partner, bank, sepa_mandate, news_subscription):

        return {'profile':{
            "id": user.oauth_uid,
            "odoo_res_users_id": user.id,
            "odoo_res_partner_id": user.partner_id.id,
            "name": user.firstname,
            "surname1": user.lastname,
            "surname2": "",
            "birth_date": partner.birthdate_date and partner.birthdate_date.strftime("%Y-%m-%d") or "",
            "gender": partner.gender or "",
            "vat": partner.vat or "",
            "contact_info": {
                "email": partner.email or "",
                "phone": partner.mobile or partner.phone or "",
                "street": partner.street or "",
                "postal_code": partner.zip or "",
                "city": partner.city or "",
                "state": partner.state_id and partner.state_id.name or "",
                "country": partner.country_id and partner.country_id.name or ""
            },
            "language": partner.lang and partner.lang.split('_')[0] or "",
            "payment_info": {
                "iban": bank and bank.acc_number or "",
                "sepa_accepted": sepa_mandate
            },
            "suscriptions": {
                "community_news": news_subscription
            }
        }}

    def _prepare_get(self, params):
        domain = [('oauth_uid','=',params.get('id'))]
        return domain 
