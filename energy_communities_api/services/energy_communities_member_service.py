from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import Component

from ..schemas import (
    CommunityInfo,
    CommunityInfoListResponse,
    MemberInfo,
    MemberInfoResponse,
    PaginationLimits,
)
from ..schemas.base import PagingParam
from ..utils import api_info, list_response, single_response


class MemberApiService(Component):
    _inherit = "base.rest.service"
    _name = "member.api.service"
    _collection = "energy_communities_member.api.services"
    _usage = "me"
    _description = """
        CE Member roles requests
    """
    _work_on_model = "res.partner"

    def __init__(self, *args):
        super().__init__(*args)

    @restapi.method(
        [(["/"], "GET")],
        output_param=PydanticModel(MemberInfoResponse),
    )
    def me(self):
        with api_info(self.env, self._work_on_model, MemberInfo) as component:
            member_info = component.get_member_info(self.env.user.partner_id)
        return single_response(request, MemberInfoResponse, member_info)

    @restapi.method(
        [(["/communities"], "GET")],
        input_param=PydanticModel(PagingParam),
        output_param=PydanticModel(CommunityInfoListResponse),
    )
    def communities(self, paging_param):
        with api_info(self.env, self._work_on_model, CommunityInfo) as component:
            member_communities = component.get_member_communities(
                self.env.user.partner_id
            )
        return list_response(
            request,
            CommunityInfoListResponse,
            member_communities or [],
            PaginationLimits(
                limit=paging_param.page_size,
                offset=(paging_param.page - 1) * paging_param.page_size,
                page=paging_param.page,
            ),
        )
