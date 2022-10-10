import logging, json
from odoo.addons.base_rest import restapi
from werkzeug.exceptions import BadRequest, NotFound
from odoo.addons.base_rest.http import wrapJsonException
from odoo.addons.component.core import Component
from odoo import _
from . import schemas

_logger = logging.getLogger(__name__)


class MemberProfileService(Component):
    _inherit = "base.rest.private_abstract_service"
    _name = "ce.member.profile.services"
    _collection = "ce.services"
    _usage = "profile"
    _description = """
        CE Member profile requests
    """
    @restapi.method(
        [(["/<string:keycloak_id>"], "GET")],
        output_param=restapi.CerberusValidator("_validator_return_get"),
        auth="api_key",
    )
    def get(self, _keycloak_id):
        user, partner, partner_bank, sepa_mandate = self._get_profile_objs(_keycloak_id)
        return self._to_dict(user, partner, partner_bank, sepa_mandate)
    
    def _validator_return_get(self):
        return schemas.S_PROFILE_RETURN_GET

    @restapi.method(
        [(["/<string:keycloak_id>"], "PUT")],
        input_param=restapi.CerberusValidator("_validator_update"),
        output_param=restapi.CerberusValidator("_validator_return_update"),
        auth="api_key",
    )
    def update(self, _keycloak_id, **params):
        user, partner, partner_bank, sepa_mandate = self._get_profile_objs(_keycloak_id)
        active_langs = self.env['res.lang'].search([('active','=', True)])
        active_code_langs = [l.code.split('_')[0] for l in active_langs]

        if params.get('language').lower() not in active_code_langs:
            raise wrapJsonException(
                BadRequest(),
                include_description=False,
                extra_info={'message': _("This language code %s is not active in Odoo. Active ones: %s") % (
                    params.get('language').lower(),
                    str(active_code_langs))}
            )

        target_lang = [l for l in active_langs if l.code.split('_')[0] == params.get('language').lower()][0]
        if partner.lang != target_lang.code:
            partner.sudo().write({'lang':target_lang.code})

        #also update lang in KeyCloack related user throw API call
        try:
            user.update_user_data_to_keyckoack(['lang'])
        except Exception as ex:
            details = (ex and hasattr(ex, 'name') and " Details: {}".format(ex.name)) or ''
            raise wrapJsonException(
                BadRequest(),
                include_description=False,
                extra_info={
                    'message': _("Unable to update the lang in Keycloak for the related KC user ID: {}.{}").format(
                        user.oauth_uid,
                        details),
                    'code': 500,
                })

        return self._to_dict(user, partner, partner_bank, sepa_mandate)

    def _validator_update(self):
        return schemas.S_PROFILE_PUT

    def _validator_return_update(self):
        return schemas.S_PROFILE_RETURN_PUT

    @staticmethod
    def _to_dict(user, partner, bank, sepa_mandate):

        return {'profile':{
            "keycloak_id": user.oauth_uid,
            "odoo_res_users_id": user.id,
            "odoo_res_partner_id": user.partner_id.id,
            "name": user.firstname,
            "surname": user.lastname,
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
            "role": user.ce_role or "",
        }}

    def _get_profile_objs(self, _keycloak_id):
        user = self.env["res.users"].sudo().search([('oauth_uid','=',_keycloak_id)])
        if not user:
            raise wrapJsonException(
                BadRequest(),
                include_description=False,
                extra_info={'message': _("No Odoo User found for KeyCloak user id %s") % _keycloak_id}
            )

        partner = user.partner_id or None
        if not partner:
            raise wrapJsonException(
                BadRequest(),
                include_description=False,
                extra_info={'message': _("No Odoo Partner found for Odoo user with login username %s") % user.login}
            )

        partner_bank = self.env['res.partner.bank'].sudo().search([
                ('partner_id', '=', partner.id), ('company_id', '=', partner.company_id.id)
            ], order="sequence asc", limit=1) or None

        sepa_mandate = partner_bank and any([sm.id for sm in partner_bank.mandate_ids if sm.state == 'valid']) or False

        return user, partner, partner_bank, sepa_mandate
