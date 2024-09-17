from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import Component

from ..schemas import (
    DEFAULT_PAGE_SIZE,
    CommunityInfo,
    CommunityInfoListResponse,
    CommunityServiceInfoListResponse,
    CommunityServiceMetricsInfoListResponse,
    MemberInfo,
    MemberInfoResponse,
)
from ..schemas.base import PagingParam, QueryParams
from ..utils import api_info, list_response, single_response


class MemberApiService(Component):
    _inherit = ["base.rest.service", "api.service.utils"]
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
            self.env,
            self._work_on_model,
            MemberInfo,
            community_id,
        ) as component:
            member_info = component.get_member_info(component.env.user.partner_id)
        return single_response(request, MemberInfoResponse, member_info)

    @restapi.method(
        [(["/communities"], "GET")],
        input_param=PydanticModel(PagingParam),
        output_param=PydanticModel(CommunityInfoListResponse),
    )
    def communities(self, paging_param):
        paging = self._get_pagination_limits(paging_param)
        with api_info(
            self.env, self._work_on_model, CommunityInfo, paging=paging
        ) as component:
            total_member_comunities = component.total_member_communities(
                self.env.user.partner_id
            )
            member_communities = component.get_member_communities(
                self.env.user.partner_id,
            )
        return list_response(
            request,
            CommunityInfoListResponse,
            member_communities,
            total_member_comunities,
            paging,
        )

    @restapi.method(
        [(["/community_services"], "GET")],
        input_param=PydanticModel(PagingParam),
        output_param=PydanticModel(CommunityServiceInfoListResponse),
    )
    def community_services_info(self, query_params):
        self._validate_headers()
        community_id = request.httprequest.headers.get("CommunityId")
        paging = self._get_pagination_limits(query_params)
        with api_info(
            self.env,
            self._work_on_model,
            CommunityInfo,
            paging=paging,
            community_id=community_id,
        ) as component:
            total_member_services = component.total_member_active_community_services(
                self.env.user.partner_id
            )
            member_community_services = component.get_member_community_services(
                self.env.user.partner_id
            )
        return list_response(
            request,
            CommunityServiceInfoListResponse,
            member_community_services,
            total_member_services,
            paging,
        )

    @restapi.method(
        [(["/community_services/metrics"], "GET")],
        input_param=PydanticModel(QueryParams),
        output_param=PydanticModel(CommunityServiceMetricsInfoListResponse),
    )
    def community_service_metrics_info(self, query_params):
        self._validate_headers()
        community_id = request.httprequest.headers.get("CommunityId")
        paging = self._get_pagination_limits(query_params)
        date_from, date_to = self._get_dates_range(query_params)
        with api_info(
            self.env,
            self._work_on_model,
            CommunityInfo,
            paging=paging,
            community_id=community_id,
        ) as component:
            total_member_services = component.total_member_active_community_services(
                self.env.user.partner_id
            )
            member_community_service_metrics = (
                component.get_member_community_services_metrics(
                    self.env.user.partner_id, date_from, date_to
                )
            )
        return list_response(
            request,
            CommunityServiceMetricsInfoListResponse,
            member_community_service_metrics,
            total_member_services,
            paging,
        )
