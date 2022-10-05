import logging, json
from odoo.addons.base_rest import restapi
from werkzeug.exceptions import BadRequest, NotFound
from odoo.addons.base_rest.http import wrapJsonException
from odoo.addons.component.core import Component
from odoo import _
from . import schemas

_logger = logging.getLogger(__name__)

class MemberService(Component):
    _inherit = "base.rest.private_abstract_service"
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
        user, partner, role, email = self._get_member_profile_objs(_keycloak_id)
        return self._to_dict(user, partner, role, email)
    
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

        user, partner, actual_role, email = self._get_member_profile_objs(_keycloak_id)
        ce_roles_map = user.ce_user_roles_mapping()

        new_role = params['role']

        if new_role not in ce_roles_map.keys():
            valid_roles = [item[0] for item in self.env['res.users'].USER_CE_ROLE_NAMES_SELECTION]
            raise wrapJsonException(
                BadRequest(),
                include_description=False,
                extra_info={
                    'message': _("The role '{}' is not a valid one, it must be one of: {}").format(
                        params['role'],
                        valid_roles),
                    'code': 500,
                    }
            )

        if new_role != actual_role:

            RoleLineSudo = self.env['res.users.role.line'].sudo()

            for role_line in user.role_line_ids:
                role_id = role_line.role_id.id
                if role_id in [r['odoo_role_id'] for r in ce_roles_map.values()]:
                    role_line.sudo().unlink()

            RoleLineSudo.create({'user_id': user.id, 'role_id': ce_roles_map[new_role]['odoo_role_id']})

            if not user.company_id.check_ce_has_admin():
                raise wrapJsonException(
                    BadRequest(),
                    include_description=False,
                    extra_info={
                        'message': _("Unable to change the member role to '{}', because the company would remain without any 'CE Admin' member").format(new_role),
                        'code': 500,
                        }
                )

            #also update KeyCloack GROUP acordingly throw API call
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

        return self._to_dict(user, partner, new_role, email)

    def _prepare_create(self, params):
        """Prepare a writable dictionary of values"""
        return {
            "company_id": params["company_id"],
            "user_id": params["user_id"],
            "target_company_id": params["target_company_id"],
            "target_user_id": params["target_user_id"],
            "new_role": params["new_role"],
        }

    def _validator_update(self):
        return schemas.S_MEMBER_PROFILE_PUT

    def _validator_return_update(self):
        return schemas.S_MEMBER_PROFILE_RETURN_PUT
    

    def _get_member_profile_objs(self, _keycloak_id):
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

        role = user.ce_role or ''
        email = partner.email or False

        return user, partner, role, email


    @staticmethod
    def _to_dict(user, partner, role, email):
        return {
            'member':{
                "keycloak_id": user.oauth_uid,
                "name": user.display_name,
                "role": user.ce_role or "",
                "email": email,
            }
        }