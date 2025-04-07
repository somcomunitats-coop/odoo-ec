from odoo.exceptions import MissingError
from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import Component

from ..schemas import (
    DEFAULT_PAGE_SIZE,
    CommunityInfo,
    CommunityInfoListResponse,
    CommunityServiceInfoListResponse,
    CommunityServiceInfoResponse,
    CommunityServiceMetricsInfo,
    CommunityServiceMetricsInfoListResponse,
    CommunityServiceMetricsInfoResponse,
    EnergyPoint,
    MemberInfo,
    MemberInfoResponse,
    ProjectEnergyConsumedInfoListResponse,
    ProjectEnergyExportedInfoListResponse,
    ProjectProductionInfoListResponse,
    ProjectSelfconsumptionInfoListResponse,
)
from ..schemas.base import PagingParam, QueryParams
from ..utils import api_info, list_response, single_response


class MemberApiService(Component):
    _inherit = ["base.rest.service", "api.service.utils"]
    _name = "member.api.service"
    _collection = "energy_communities_member.api.services"
    _usage = "me"
    _description = """
        Set of endpoints that return all information about profile, communities, metrics, services from a energy community
        member perspective
    """
    _work_on_model = "res.partner"

    def __init__(self, *args):
        super().__init__(*args)

    @restapi.method(
        [(["/"], "GET")],
        output_param=PydanticModel(MemberInfoResponse),
    )
    def me(self):
        """
        Basic personal information
        """
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
        [(["/community_services/<int:service_id>"], "GET")],
        output_param=PydanticModel(CommunityServiceInfoResponse),
    )
    def communtiy_service_detail_info(self, service_id):
        self._validate_headers()
        community_id = request.httprequest.headers.get("CommunityId")
        with api_info(
            self.env,
            self._work_on_model,
            CommunityInfo,
            community_id=community_id,
        ) as component:
            service = component.get_member_community_service_detail(
                self.env.user.partner_id, service_id
            )
            if not service:
                raise MissingError(f"Community service with id {service_id} not found")
        return single_response(request, CommunityServiceInfoResponse, service)

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

    @restapi.method(
        [(["/community_services/<int:service_id>/metrics"], "GET")],
        input_param=PydanticModel(QueryParams),
        output_param=PydanticModel(CommunityServiceMetricsInfoResponse),
    )
    def community_service_metrics_details_info(
        self, service_id: int, query_params: QueryParams
    ):
        self._validate_headers()
        community_id = request.httprequest.headers.get("CommunityId")
        date_from, date_to = self._get_dates_range(query_params)
        with api_info(
            self.env,
            self._work_on_model,
            CommunityServiceMetricsInfo,
            community_id=community_id,
        ) as component:
            project = component.work.component(
                "api.info", "energy_project.project"
            ).get_project_from_service(service_id)
            if not project:
                raise MissingError(
                    f"Service with id {service_id} has not a project associated"
                )
            service_metrics = (
                component.get_member_community_services_metrics_by_service(
                    self.env.user.partner_id, service_id, date_from, date_to
                )
            )
        return single_response(
            request, CommunityServiceMetricsInfoResponse, service_metrics
        )

    @restapi.method(
        [(["/community_services/<int:service_id>/production"], "GET")],
        input_param=PydanticModel(QueryParams),
        output_param=PydanticModel(ProjectProductionInfoListResponse),
    )
    def community_service_production_info(
        self, service_id: int, query_params: QueryParams
    ):
        self._validate_headers()
        community_id = request.httprequest.headers.get("CommunityId")
        paging = self._get_pagination_limits(query_params)
        date_from, date_to = self._get_dates_range(query_params)
        with api_info(
            self.env,
            "energy_project.project",
            EnergyPoint,
            paging=paging,
            community_id=community_id,
        ) as component:
            project = component.get_project_from_service(service_id)
            if not project:
                raise MissingError(
                    f"Service with id {service_id} has not a project associated"
                )
            daily_production = component.get_project_daily_production_by_member(
                project, self.env.user.partner_id, date_from, date_to
            )
        return list_response(
            request,
            ProjectProductionInfoListResponse,
            daily_production,
            len(daily_production),
            paging,
        )

    @restapi.method(
        [(["/community_services/<int:service_id>/selfconsumption"], "GET")],
        input_param=PydanticModel(QueryParams),
        output_param=PydanticModel(ProjectSelfconsumptionInfoListResponse),
    )
    def community_service_selfconsumption_info(
        self, service_id: int, query_params: QueryParams
    ):
        self._validate_headers()
        community_id = request.httprequest.headers.get("CommunityId")
        paging = self._get_pagination_limits(query_params)
        date_from, date_to = self._get_dates_range(query_params)
        with api_info(
            self.env,
            "energy_project.project",
            EnergyPoint,
            paging=paging,
            community_id=community_id,
        ) as component:
            project = component.get_project_from_service(service_id)
            if not project:
                raise MissingError(
                    f"Service with id {service_id} has not a project associated"
                )
            daily_selfconsumption = (
                component.get_project_daily_selfconsumption_by_member(
                    project, self.env.user.partner_id, date_from, date_to
                )
            )
        return list_response(
            request,
            ProjectProductionInfoListResponse,
            daily_selfconsumption,
            len(daily_selfconsumption),
            paging,
        )

    @restapi.method(
        [(["/community_services/<int:service_id>/energy_exported"], "GET")],
        input_param=PydanticModel(QueryParams),
        output_param=PydanticModel(ProjectEnergyExportedInfoListResponse),
    )
    def community_service_energy_exported_info(
        self, service_id: int, query_params: QueryParams
    ):
        self._validate_headers()
        community_id = request.httprequest.headers.get("CommunityId")
        paging = self._get_pagination_limits(query_params)
        date_from, date_to = self._get_dates_range(query_params)
        with api_info(
            self.env,
            "energy_project.project",
            EnergyPoint,
            paging=paging,
            community_id=community_id,
        ) as component:
            project = component.get_project_from_service(service_id)
            if not project:
                raise MissingError(
                    f"Service with id {service_id} has not a project associated"
                )
            daily_selfconsumption = (
                component.get_project_daily_exported_energy_by_member(
                    project, self.env.user.partner_id, date_from, date_to
                )
            )
        return list_response(
            request,
            ProjectEnergyExportedInfoListResponse,
            daily_selfconsumption,
            len(daily_selfconsumption),
            paging,
        )

    @restapi.method(
        [(["/community_services/<int:service_id>/energy_consumed"], "GET")],
        input_param=PydanticModel(QueryParams),
        output_param=PydanticModel(ProjectEnergyConsumedInfoListResponse),
    )
    def community_service_energy_consumed_info(
        self, service_id: int, query_params: QueryParams
    ):
        self._validate_headers()
        community_id = request.httprequest.headers.get("CommunityId")
        paging = self._get_pagination_limits(query_params)
        date_from, date_to = self._get_dates_range(query_params)
        with api_info(
            self.env,
            "energy_project.project",
            EnergyPoint,
            paging=paging,
            community_id=community_id,
        ) as component:
            project = component.get_project_from_service(service_id)
            if not project:
                raise MissingError(
                    f"Service with id {service_id} has not a project associated"
                )
            daily_selfconsumption = (
                component.get_project_daily_consumed_energy_by_member(
                    project, self.env.user.partner_id, date_from, date_to
                )
            )
        return list_response(
            request,
            ProjectEnergyConsumedInfoListResponse,
            daily_selfconsumption,
            len(daily_selfconsumption),
            paging,
        )
