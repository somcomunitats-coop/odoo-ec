from werkzeug.exceptions import Unauthorized

from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import (
    PydanticModel,
    PydanticModelList,
)
from odoo.addons.component.core import Component

from ..schemas import (
    DEFAULT_PAGE_SIZE,
    MemberCommunitiesResponse,
    MemberCommunity,
    MemberInfo,
    MemberInfoResponse,
    PaginationLimits,
)
from ..schemas.base import PagingParam
from ..utils import collection_response, single_response


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
        output_param=PydanticModel(MemberInfoResponse),
    )
    def me(self):
        return single_response(
            request, MemberInfoResponse, MemberInfo.from_orm(self.env.user.partner_id)
        )

    @restapi.method(
        [(["/communities"], "GET")],
        input_param=PydanticModel(PagingParam),
        # output_param=PydanticModelList(MemberComunitiesResponse),
    )
    def communities(self, paging_param):
        paging = PaginationLimits(
            limit=paging_param.page_size,
            offset=(paging_param.page - 1) * paging_param.page_size,
            page=paging_param.page,
        )
        ret = collection_response(
            request,
            MemberCommunitiesResponse,
            self._get_member_communities(),
            100,
            paging,
        )
        return ret

    def _get_member_communities(self):
        ret = []
        memberships = self.env["cooperative.membership"].search(
            [("partner_id", "=", self.env.user.partner_id.id)]
        )
        for membership in memberships:
            membership_company = membership.company_id
            ret.append(MemberCommunity(name=membership_company.name).dict())
        return ret
