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


class MemberService(Component):
    _inherit = "base.rest.service"
    _name = "ce.member.services"
    _collection = "ce.services"
    _usage = "member"
    _description = """
        CE Member roles requests
    """

    @restapi.method(
        [(["/<string:keycloak_id>"], "GET")],
        output_param=restapi.CerberusValidator("_validator_return_get"),
        auth="api_key",
    )
    def get(self, _keycloak_id):
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
                user, partner, kc_role, email = self._get_member_profile_objs(
                    _keycloak_id
                )
                return self._to_dict(user, partner, kc_role, email)
            else:
                raise wrapJsonException(
                    Unauthorized(),
                    include_description=False,
                    extra_info={
                        "message": _(
                            "The received oauth KeyCloak token have not been validated by KeyCloak : {}"
                        ).format(received_token),
                        "code": 401,
                    },
                )
        else:
            raise wrapJsonException(
                Unauthorized(),
                include_description=False,
                extra_info={
                    "message": _("Authorization token not found"),
                    "code": 500,
                },
            )

    def _validator_return_get(self):
        return schemas.S_MEMBER_PROFILE_RETURN_GET

    @restapi.method(
        [(["/<string:keycloak_id>"], "PUT")],
        input_param=restapi.CerberusValidator("_validator_update"),
        output_param=restapi.CerberusValidator("_validator_return_update"),
        auth="api_key",
    )
    def update(self, _keycloak_id, **params):
        _logger.info("Requested role update, user: {}".format(_keycloak_id))
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
                user, partner, actual_role, email = self._get_member_profile_objs(
                    _keycloak_id
                )
                role = self.env["res.users.role"].search(
                    [("code", "=", params["role"])]
                )

                if not role:
                    raise wrapJsonException(
                        BadRequest(),
                        include_description=False,
                        extra_info={
                            "message": _(
                                "The role code '{}' is not a valid one"
                            ).format(params["role"]),
                            "code": 500,
                        },
                    )
                if user.role_line_ids:
                    user.role_line_ids.write({"role_id": role.id})
                else:
                    user.role_line_ids.create([{"role_id": role.id}])
                return self._to_dict(user, partner, params["role"], email)
            else:
                raise wrapJsonException(
                    Unauthorized(),
                    include_description=False,
                    extra_info={
                        "message": _(
                            "The received oauth KeyCloak token have not been validated by KeyCloak : {}"
                        ).format(received_token),
                        "code": 401,
                    },
                )
        else:
            raise wrapJsonException(
                Unauthorized(),
                include_description=False,
                extra_info={
                    "message": _("Authorization token not found"),
                    "code": 500,
                },
            )

    def _validator_update(self):
        return schemas.S_MEMBER_PROFILE_PUT

    def _validator_return_update(self):
        return schemas.S_MEMBER_PROFILE_RETURN_PUT

    def _get_member_profile_objs(self, _keycloak_id):
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

        email = partner.email or False

        return user, partner, user.get_role_codes(), email

    @staticmethod
    def _to_dict(user, partner, kc_role, email):
        return {
            "member": {
                "keycloak_id": user.oauth_uid,
                "name": user.display_name,
                "role": kc_role or "",
                "email": email,
            }
        }
