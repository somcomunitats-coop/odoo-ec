from werkzeug.exceptions import Unauthorized

from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import (
    PydanticModel,
    PydanticModelList,
)
from odoo.addons.component.core import Component

from ..schemas import MemberCommunitiesResponse, MemberInfo, MemberInfoResponse
from ..utils import single_response


class MemberApiService(Component):
    _inherit = "base.rest.service"
    _name = "member.api.service"
    _collection = "energy_communities_member.api.services"
    _usage = "me"
    _description = """
        CE Member roles requests
    """

    @restapi.method(
        [(["/"], "GET")],
        # output_param=PydanticModelList(MemberInfoResponse),
    )
    def me(self):
        return single_response(
            request, MemberInfoResponse, MemberInfo.from_orm(self.env.user.partner_id)
        )

    @restapi.method(
        [(["/communities"], "GET")],
        # output_param=PydanticModelList(MemberComunitiesResponse),
    )
    def communities(self):
        return single_response(
            request,
            MemberCommunitiesResponse,
            self._get_member_communities(self.env.user.partner_id),
        )
