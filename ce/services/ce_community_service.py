import logging, json
from odoo.addons.base_rest import restapi
from werkzeug.exceptions import BadRequest, NotFound
from odoo.addons.base_rest.http import wrapJsonException
from odoo.addons.component.core import Component
from odoo import _
from datetime import datetime
from . import schemas

_logger = logging.getLogger(__name__)


class CommunityService(Component):
    _inherit = "base.rest.private_abstract_service"
    _name = "ce.community.services"
    _collection = "ce.services"
    _usage = "community"
    _description = """
        CE community requests
    """
    @restapi.method(
        [(["/<int:odoo_company_id>/members"], "GET")],
        output_param=restapi.CerberusValidator("_validator_return_community_members_get"),
        auth="api_key",
    )
    def get(self, _odoo_company_id):
        company_id = self.env['res.company'].get_real_ce_company_id(_odoo_company_id)

        if not company_id:
            raise wrapJsonException(
                BadRequest(),
                include_description=False,
                extra_info={'message': _("No Odoo Company found for odoo_company_id %s") % _odoo_company_id}
            )

        member_users = company_id.get_ce_members()
        return self._to_dict_members(member_users)

    def _validator_return_community_members_get(self):
        return schemas.S_COMMUNITY_MEMBERS_RETURN_GET

    @staticmethod
    def _to_dict_members(users):
        resp = {'members':[]}
        for user in users:
            resp['members'].append({
                "name": '{} {}'.format(user.firstname,user.lastname,),
                "role": user.ce_role or "",
                "email": user.email or "",
                "keycloak_id": user.oauth_uid,
            })
        return resp

    @restapi.method(
        [(["/<int:odoo_company_id>"], "GET")],
        output_param=restapi.CerberusValidator("_validator_return_community_get"),
        auth="api_key",
    )
    def get(self, _odoo_company_id):
        company_id = self.env['res.company'].get_real_ce_company_id(_odoo_company_id)

        if not company_id:
            raise wrapJsonException(
                BadRequest(),
                include_description=False,
                extra_info={'message': _("No Odoo Company found for odoo_company_id %s") % _odoo_company_id}
            )

        return self._to_dict_community(company_id)

    def _validator_return_community_get(self):
        return schemas.S_COMMUNITY_RETURN_GET

    @staticmethod
    def _to_dict_community(company):

        resp = {
            'id': company.id,
            'name': company.name,
            'birth_date': company.foundation_date and company.foundation_date.strftime('%Y-%m-%d') or '',
            'members':[],
            'contact_info':{
                'street': company.street or '',
                'postal_code': company.zip or '',
                'city': company.city or '',
                'state': company.state_id.name or '',
                'country': company.country_id.name or '',
                'phone': company.phone or '',
                'email': company.email or '',
                'telegram': company.social_telegram or ''},
            'active_services': []
            }

        resp.update(CommunityService._to_dict_members(company.get_ce_members()))
        resp.update({'active_services': company.get_active_services()})

        return resp
