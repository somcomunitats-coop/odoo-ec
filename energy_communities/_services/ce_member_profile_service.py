import logging

from keycloak import KeycloakOpenID
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized

from odoo import _
from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest.http import wrapJsonException
from odoo.addons.component.core import Component

from . import schemas

_logger = logging.getLogger(__name__)


class MemberProfileService(Component):
    _inherit = "base.rest.service"
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
        if (
            headers.get("Authorization")
            and headers.get("Authorization")[:7] == "Bearer "
        ):
            received_token = headers.get("Authorization")[7:]

            keycloak_admin_provider = self.env.ref(
                "energy_communities.keycloak_admin_provider"
            )
            keycloak_openid = KeycloakOpenID(
                server_url=keycloak_admin_provider.root_endpoint,
                client_id=keycloak_admin_provider.client_id,
                realm_name=keycloak_admin_provider.realm_name,
                client_secret_key=keycloak_admin_provider.client_secret,
            )
            validation_received_token = keycloak_openid.introspect(received_token)
            if validation_received_token["active"]:
                _keycloak_id = validation_received_token.get("sub")
            else:
                raise wrapJsonException(
                    Unauthorized(),
                    include_description=False,
                    extra_info={
                        "message": _(
                            "The received oauth KeyCloak token have not been validated by KeyCloak : {}"
                        ).format(validation_received_token),
                        "code": 401,
                    },
                )
            if not _keycloak_id:
                raise wrapJsonException(
                    Unauthorized(),
                    include_description=False,
                    extra_info={
                        "message": _(
                            "Unable to validate the received oauth KeyCloak token: {}"
                        ).format(validation_received_token),
                        "code": 500,
                    },
                )

            user, partner, companies_data = self._get_profile_objs(_keycloak_id)
            return self._to_dict(user, partner, companies_data)
        else:
            raise wrapJsonException(
                Unauthorized(),
                include_description=False,
                extra_info={
                    "message": _("Authorization token not found"),
                    "code": 500,
                },
            )

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
        active_langs = self.env["res.lang"].search([("active", "=", True)])
        active_code_langs = [l.code.split("_")[0] for l in active_langs]

        if params.get("language").lower() not in active_code_langs:
            raise wrapJsonException(
                AuthenticationFailed(),
                include_description=False,
                extra_info={
                    "message": _(
                        "This language code %s is not active in Odoo. Active ones: %s"
                    )
                    % (params.get("language").lower(), str(active_code_langs))
                },
            )

        target_lang = [
            l
            for l in active_langs
            if l.code.split("_")[0] == params.get("language").lower()
        ][0]
        if partner.lang != target_lang.code:
            partner.sudo().write({"lang": target_lang.code})

        # also update lang in KeyCloack related user throw API call
        try:
            user.update_user_data_to_keyckoack(["lang"])
        except Exception as ex:
            details = (
                ex and hasattr(ex, "name") and " Details: {}".format(ex.name)
            ) or ""
            raise wrapJsonException(
                BadRequest(),
                include_description=False,
                extra_info={
                    "message": _(
                        "Unable to update the lang in Keycloak for the related KC user ID: {}.{}"
                    ).format(user.oauth_uid, details),
                    "code": 500,
                },
            )

        return self._to_dict(user, partner, companies_data)

    def _validator_update(self):
        return schemas.S_PROFILE_PUT

    def _validator_return_update(self):
        return schemas.S_PROFILE_RETURN_PUT

    @staticmethod
    def _to_dict(user, partner, companies_data):
        return {
            "profile": {
                "keycloak_id": user.oauth_uid,
                "odoo_res_users_id": user.id,
                "odoo_res_partner_id": user.partner_id.id,
                "name": user.firstname,
                "surname": user.lastname,
                "birth_date": partner.birthdate_date
                and partner.birthdate_date.strftime("%Y-%m-%d")
                or "",
                "gender": partner.gender or "",
                "vat": partner.vat or "",
                "contact_info": {
                    "email": partner.email or "",
                    "phone": partner.mobile or partner.phone or "",
                    "street": partner.street or "",
                    "postal_code": partner.zip or "",
                    "city": partner.city or "",
                    "state": partner.state_id and partner.state_id.name or "",
                    "country": partner.country_id and partner.country_id.name or "",
                },
                "language": partner.lang and partner.lang.split("_")[0] or "",
                "communities": companies_data,
            }
        }

    def _get_profile_objs(self, _keycloak_id):
        user = self.env["res.users"].sudo().search([("oauth_uid", "=", _keycloak_id)])

        if not user:
            raise wrapJsonException(
                BadRequest(),
                include_description=False,
                extra_info={
                    "message": _("No Odoo User found for KeyCloak user id %s")
                    % _keycloak_id
                },
            )

        partner = user.partner_id or None
        if not partner:
            raise wrapJsonException(
                BadRequest(),
                include_description=False,
                extra_info={
                    "message": _(
                        "No Odoo Partner found for Odoo user with login username %s"
                    )
                    % user.login
                },
            )

        companies_data = []
        login_provider_id = self.env.ref("energy_communities.keycloak_login_provider")
        for company_id in user.company_ids:
            partner_bank = (
                self.env["res.partner.bank"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", partner.id),
                        ("company_id", "=", company_id.id),
                    ],
                    order="sequence asc",
                    limit=1,
                )
                or None
            )

            sepa_mandate = (
                partner_bank
                and any(
                    [sm.id for sm in partner_bank.mandate_ids if sm.state == "valid"]
                )
                or False
            )
            role_code = ""
            if user.role_line_ids:
                role_code = user.role_line_ids[0].role_id.code
            companies_data.append(
                {
                    "id": company_id.id,
                    "name": company_id.name,
                    "role": role_code,
                    "public_web_landing_url": "https://somcomunitats.coop/ce/comunitat-energetica-prova/",
                    # TODO Get landing from map
                    "keycloak_odoo_login_url": login_provider_id.get_auth_link() or "",
                    "payment_info": {
                        "iban": partner_bank and partner_bank.acc_number or "",
                        "sepa_accepted": sepa_mandate,
                    },
                }
            )

        return user, partner, companies_data
