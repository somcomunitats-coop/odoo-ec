import logging, json
from odoo.addons.base_rest import restapi
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized
from odoo.addons.base_rest.http import wrapJsonException
from odoo.addons.component.core import Component
from odoo.http import request
from odoo import _
from keycloak import KeycloakOpenID
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
        if headers.get('Authorization') and headers.get('Authorization')[:7] == 'Bearer ':
            received_token = headers.get('Authorization')[7:]

            keycloak_admin_provider = self.env.ref('energy_communities.keycloak_admin_provider')
            keycloak_openid = KeycloakOpenID(server_url=keycloak_admin_provider.root_endpoint,
                                             client_id=keycloak_admin_provider.client_id,
                                             realm_name=keycloak_admin_provider.realm_name,
                                             client_secret_key=keycloak_admin_provider.client_secret)
            validation_received_token = keycloak_openid.introspect(received_token)
            if validation_received_token['active']:
                user, partner, kc_role, email = self._get_member_profile_objs(_keycloak_id)
                return self._to_dict(user, partner, kc_role, email)
            else:
                raise wrapJsonException(
                    Unauthorized(),
                    include_description=False,
                    extra_info={
                        'message': _(
                            "The received oauth KeyCloak token have not been validated by KeyCloak : {}").format(
                            received_token),
                        'code': 401,
                    })
        else:
            raise wrapJsonException(
                Unauthorized(),
                include_description=False,
                extra_info={
                    'message': _("Authorization token not found"),
                    'code': 500,
                })

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

        user, partner, actual_kc_role, email = self._get_member_profile_objs(_keycloak_id)
        ce_roles_map = self.env['res.users'].ce_user_roles_mapping()
        kc_role_list = [r['kc_role_name'] for r in ce_roles_map.values()]
        new_kc_role = params['role']

        if new_kc_role not in kc_role_list:
            raise wrapJsonException(
                BadRequest(),
                include_description=False,
                extra_info={
                    'message': _("The role '{}' is not a valid one, it must be one of: {}").format(
                        params['role'],
                        kc_role_list),
                    'code': 500,
                }
            )

        if new_kc_role != actual_kc_role:

            RoleLineSudo = self.env['res.users.role.line'].sudo()

            # reset/delete all the existing odoo role ids of this user (only the ones related to the CE module)
            for role_line in user.role_line_ids:
                role_id = role_line.role_id.id
                if role_id in [r['odoo_role_id'] for r in ce_roles_map.values()]:
                    role_line.sudo().unlink()

            # assign to the user the new odoo role
            new_odoo_role = [v['odoo_role_id'] for k, v in ce_roles_map.items() if v['kc_role_name'] == new_kc_role]
            RoleLineSudo.create({
                'user_id': user.id,
                'role_id': new_odoo_role[0],
                'company_id': user.company_id.id,
            })

            if not user.company_id.check_ce_has_admin():
                raise wrapJsonException(
                    BadRequest(),
                    include_description=False,
                    extra_info={
                        'message': _(
                            "Unable to change the user role to '{}', because the company would remain without any 'CE Admin' member").format(
                            new_kc_role),
                        'code': 500,
                    }
                )

            # also update KeyCloack GROUP acordingly throw API call
            try:
                user.update_user_data_to_keyckoack(['groups'])
            except Exception as ex:
                details = (ex and hasattr(ex, 'name') and " Details: {}".format(ex.name)) or ''
                raise wrapJsonException(
                    BadRequest(),
                    include_description=False,
                    extra_info={
                        'message': _("Unable to update the role in Keycloak for the related KC user ID: {}.{}").format(
                            user.oauth_uid,
                            details),
                        'code': 500,
                    })

        return self._to_dict(user, partner, new_kc_role, email)

    def _validator_update(self):
        return schemas.S_MEMBER_PROFILE_PUT

    def _validator_return_update(self):
        return schemas.S_MEMBER_PROFILE_RETURN_PUT

    def _get_member_profile_objs(self, _keycloak_id):
        user = self.env["res.users"].sudo().search([('oauth_uid', '=', _keycloak_id)])
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

        email = partner.email or False

        return user, partner, user.get_role_codes(), email

    @staticmethod
    def _to_dict(user, partner, kc_role, email):
        return {
            'member': {
                "keycloak_id": user.oauth_uid,
                "name": user.display_name,
                "role": kc_role or "",
                "email": email,
            }
        }
