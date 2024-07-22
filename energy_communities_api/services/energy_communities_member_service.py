from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import Component

from ..schemas import (
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

    def __init__(self, *args):
        super().__init__(*args)
        self.api_info = api_info(
            self.env,
            MemberInfo,
            "res.partner",
            self.env.user.partner_id.id,
        )

    @restapi.method(
        [(["/"], "GET")],
        output_param=PydanticModel(MemberInfoResponse),
    )
    def me(self):
        return single_response(request, MemberInfoResponse, self.api_info.get())

    @restapi.method(
        [(["/communities"], "GET")],
        input_param=PydanticModel(PagingParam),
        output_param=PydanticModel(CommunityInfoListResponse),
    )
    def communities(self, paging_param):
        return list_response(
            request,
            CommunityInfoListResponse,
            self.api_info.get_communities(),
            PaginationLimits(
                limit=paging_param.page_size,
                offset=(paging_param.page - 1) * paging_param.page_size,
                page=paging_param.page,
            ),
        )
