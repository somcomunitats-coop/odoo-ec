from odoo import models
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
        # 1.- Pure component way
        # coll = self.env['res.partner.collection'].browse(self.env.user.partner_id.id)
        # with coll.work_on('res.partner') as member_info_worker:
        #     member_info_worker.component(usage="member.info").get_member_info()
        # 2.- Service inheritance way
        # return single_response(
        #     request, MemberInfoResponse, self._get_member_info()
        # )
        # 3.- AbstractModel way
        return single_response(
            request,
            MemberInfoResponse,
            self.env["member.info.backend.abstract"].get_member_info(
                self.env.user.partner_id
            ),
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


class MemberInfoBackend(Component):
    _inherit = "member.api.service"

    def _get_member_info(self):
        return MemberInfo.from_orm(self.env.user.partner_id)

    def _get_member_communities(self):
        ret = []
        memberships = self.env["cooperative.membership"].search(
            [("partner_id", "=", self.env.user.partner_id.id)]
        )
        for membership in memberships:
            ret.append(MemberCommunity.from_orm(membership.company_id))
        return ret


class MemberInfoBackendAbstract(models.AbstractModel):
    _name = "member.info.backend.abstract"

    # def __init__(self, record):
    #     self.record = record

    def get_member_info(self, record):
        return MemberInfo.from_orm(record)

    def _get_member_communities(self):
        ret = []
        memberships = self.env["cooperative.membership"].search(
            [("partner_id", "=", self.record.id)]
        )
        for membership in memberships:
            ret.append(MemberCommunity.from_orm(membership.company_id))
        return ret
