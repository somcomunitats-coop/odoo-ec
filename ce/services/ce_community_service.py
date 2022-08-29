import logging, json
from odoo.addons.base_rest import restapi
from werkzeug.exceptions import BadRequest, NotFound
from odoo.addons.base_rest.http import wrapJsonException
from odoo.addons.component.core import Component
from odoo import _
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

        member_users = company_id.get_ce_members()
        return self._to_dict(member_users)
    
    def _validator_return_community_get(self):
        return schemas.S_COMMUNITY_MEMBERS_RETURN_GET

    @staticmethod
    def _to_dict(users):
        resp = {'members':[]}
        for user in users:
            resp['members'].append({
                "name": '{} {}'.format(user.firstname,user.lastname,),
                "rol": user.ce_role or "",
                "email": user.email or ""
            })
        return resp
