import logging, json
from odoo.addons.base_rest import restapi
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound
from odoo.addons.base_rest.http import wrapJsonException
from odoo.addons.component.core import Component
from odoo import _
from . import schemas
from odoo.http import request

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
        [(["/"], "GET")],
        output_param=restapi.CerberusValidator("_validator_return_get"),
        auth="api_key",
    )
    def get(self):
        headers = request.httprequest.headers
        _keycloak_id = None
        if ((not _keycloak_id) and headers.get('Authorization') and headers.get('Authorization')[:7] == 'Bearer '):
            received_token = headers.get('Authorization').replace(headers.get('Authorization')[:7],'')

            realm_0_login_provider = self.env.ref('ce.platform_login_keycloak_provider')
            wiz_vals = {
                'provider_id': realm_0_login_provider.id,
                'endpoint': realm_0_login_provider.users_endpoint,
                'user': realm_0_login_provider.superuser,
                'pwd': realm_0_login_provider.superuser_pwd,
                'login_match_key': 'username:login'
            }
            realm_login_wiz = self.env['auth.keycloak.sync.wiz'].sudo().create(wiz_vals)
            realm_login_wiz._validate_setup()

            on_fly_token = realm_login_wiz._get_token()
            #validation_on_fly = self.env['res.users']._keycloak_validate(realm_0_login_provider, on_fly_token)
            validation_received_token = self.env['res.users']._keycloak_validate(realm_0_login_provider, received_token)
            if validation_received_token.get('sub'):
                _keycloak_id = validation_received_token.get('sub')
            else:
                raise wrapJsonException(
                Unauthorized(),
                include_description=False,
                extra_info={
                    'message': _("The received oauth KeyCloak token have not been validated by KeyCloak : {}").format(
                        validation_received_token),
                    'code': 401,
                })
            #import pudb; pu.db
        if not _keycloak_id:
                raise wrapJsonException(
                Unauthorized(),
                include_description=False,
                extra_info={
                    'message': _("Unable to validate the received oauth KeyCloak token: {}").format(
                        validation_received_token),
                    'code': 500,
                })

        user, partner, companies_data = self._get_profile_objs(_keycloak_id)
        return self._to_dict(user, partner, companies_data)

    @restapi.method(
        [(["/<string:keycloak_id>"], "GET")],
        output_param=restapi.CerberusValidator("_validator_return_get"),
        auth="api_key",
    )
    def get_by_kc_user_id(self, _keycloak_id):
        user, partner, companies_data = self._get_profile_objs(_keycloak_id)
        return self._to_dict(user, partner, companies_data)


    def _validator_return_get(self):
        return schemas.S_PROFILE_RETURN_GET

    @restapi.method(
        [(["/<string:keycloak_id>"], "PUT")],
        input_param=restapi.CerberusValidator("_validator_update"),
        output_param=restapi.CerberusValidator("_validator_return_update"),
        auth="api_key",
    )
    def update(self, _keycloak_id, **params):
        user, partner, companies_data = self._get_profile_objs(_keycloak_id)
        active_langs = self.env['res.lang'].search([('active','=', True)])
        active_code_langs = [l.code.split('_')[0] for l in active_langs]

        if params.get('language').lower() not in active_code_langs:
            raise wrapJsonException(
                AuthenticationFailed(),
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

        return self._to_dict(user, partner, companies_data)

    def _validator_update(self):
        return schemas.S_PROFILE_PUT

    def _validator_return_update(self):
        return schemas.S_PROFILE_RETURN_PUT

    @staticmethod
    def _to_dict(user, partner, companies_data):

        # in case that an user don't have any odoo role assigned in odoo, we will return that it is 'CE member'
        user_ce_role = user.ce_role or 'role_ce_member'


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
            "communities": companies_data,
        }}

    def _get_profile_objs(self, _keycloak_id):
        user = self.env["res.users"].sudo().search([('oauth_uid','=',_keycloak_id)])

        #todo: on next iteration we will install the module that allow have different role per each company
        user_ce_role = user.ce_role or 'role_ce_member'

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

        companies_data = []
        for company_id in user.company_ids:

            partner_bank = self.env['res.partner.bank'].sudo().search([
                ('partner_id', '=', partner.id), ('company_id', '=', company_id.id)
            ], order="sequence asc", limit=1) or None

            sepa_mandate = partner_bank and any([sm.id for sm in partner_bank.mandate_ids if sm.state == 'valid']) or False

            companies_data.append({
                "id": company_id.id,
                "name": company_id.name,
                "role": user.ce_user_roles_mapping()[user_ce_role]['kc_role_name'] or "",
                "public_web_landing_url": company_id.get_public_web_landing_url() or '',
                "keycloak_odoo_login_url": company_id.get_keycloak_odoo_login_url() or '',
                "payment_info": {
                    "iban": partner_bank and partner_bank.acc_number or "",
                    "sepa_accepted": sepa_mandate
                },
            })

        return user, partner, companies_data
