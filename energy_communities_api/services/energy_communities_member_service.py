from odoo import _
from odoo.exceptions import ValidationError
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
        self._validate_headers()
        community_id = request.httprequest.headers.get("CommunityId")
        with api_info(
            self.env, self._work_on_model, community_id, MemberInfo
        ) as component:
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
            member_communities,
            PaginationLimits(
                limit=paging_param.page_size,
                offset=(paging_param.page - 1) * paging_param.page_size,
                page=paging_param.page,
            ),
        )

    def _validate_headers(self):
        community_id = request.httprequest.headers.get("CommunityId")
        if not community_id:
            msg = _("CommunityId header is missing")
            raise ValidationError(msg)
        try:
            int(community_id)
        except Exception:
            msg = _(f"CommunityId header has an incorrect value: {community_id}")
            raise ValidationError(msg)
