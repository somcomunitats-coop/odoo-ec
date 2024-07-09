from werkzeug.exceptions import Unauthorized

from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import Component

from ..schemas import MemberInfo, MemberInfoResponse
from ..utils import single_response


class MemberApiService(Component):
    _inherit = "base.rest.service"
    _name = "member.api.service"
    _collection = "energy_communities_member.api.services"
    _usage = "member"
    _description = """
        CE Member roles requests
    """

    @restapi.method(
        [(["/"], "GET")],
        output_param=PydanticModel(MemberInfoResponse),
    )
    def me(self):
        if not getattr(request, "jwt_partner_id", None):
            raise Unauthorized()

        member = request.env["res.partner"].browse(request.jwt_partner_id)
        member_info = MemberInfo.from_orm(member)

        return single_response(MemberInfoResponse, member_info)
