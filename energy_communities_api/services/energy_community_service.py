from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import Component

from ..schemas import (
    CommunityServiceInfo,
    CommunityServiceInfoListResponse,
    EnergyCommunityInfo,
    EnergyCommunityInfoResponse,
    QueryParams,
)
from ..utils import api_info, list_response, single_response


class EnergyCommunityApiService(Component):
    _inherit = ["base.rest.service", "api.service.utils"]
    _name = "energy_community.api.service"
    _collection = "energy_communities.api.services"
    _usage = "communities"
    _description = """
        Set of enpoints that retrieve and manage information about energy communities
    """
    _work_on_model = "res.company"

    def __init__(self, *args):
        super().__init__(*args)

    @restapi.method(
        [(["/<int:community_id>"], "GET")],
        output_param=PydanticModel(EnergyCommunityInfoResponse),
    )
    def energy_community(self, community_id):
        """
        Basic information about a energy community
        """
        self._validate_headers()
        member_community_id = request.httprequest.headers.get("CommunityId")
        with api_info(
            self.env,
            self._work_on_model,
            EnergyCommunityInfo,
            member_community_id,
        ) as component:
            community_info = component.get_energy_community_info(community_id)
        return single_response(request, EnergyCommunityInfoResponse, community_info)

    @restapi.method(
        [(["/<int:community_id>/community_services"], "GET")],
        input_param=PydanticModel(QueryParams),
        output_param=PydanticModel(CommunityServiceInfoListResponse),
    )
    def energy_community_community_services_info(
        self, community_id: int, query_params: QueryParams
    ):
        """
        Set of services that offer an energy community
        """
        self._validate_headers()
        member_community_id = request.httprequest.headers.get("CommunityId")
        paging = self._get_pagination_limits(query_params)
        with api_info(
            self.env,
            self._work_on_model,
            CommunityServiceInfo,
            member_community_id,
            paging=paging,
        ) as component:
            total_community_services = component.total_community_services(community_id)
            community_services = component.get_community_services(community_id)
        return list_response(
            request,
            CommunityServiceInfoListResponse,
            community_services,
            total_community_services,
            paging,
        )
