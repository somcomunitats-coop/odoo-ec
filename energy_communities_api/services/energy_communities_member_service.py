from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import (  # PydanticModelList,
    PydanticModel,
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
        output_param=PydanticModel(MemberCommunitiesResponse),
    )
    def communities(self, paging_param):
        return collection_response(
            request,
            MemberCommunitiesResponse,
            self._get_member_communities(),
            PaginationLimits(
                limit=paging_param.page_size,
                offset=(paging_param.page - 1) * paging_param.page_size,
                page=paging_param.page,
            ),
        )

    def _get_member_communities(self):
        ret = []
        memberships = self.env["cooperative.membership"].search(
            [("partner_id", "=", self.env.user.partner_id.id)]
        )
        for membership in memberships:
            ret.append(MemberCommunity.from_orm(membership.company_id))
        return ret
