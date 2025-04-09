from odoo.exceptions import MissingError
from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import Component

from ..schemas import (
    CommunityServiceInfo,
    CommunityServiceInfoListResponse,
    CommunityServiceInfoResponse,
    CommunityServiceMetricsInfo,
    CommunityServiceMetricsInfoListResponse,
    CommunityServiceMetricsInfoResponse,
    EnergyCommunityInfo,
    EnergyCommunityInfoResponse,
    EnergyPoint,
    ProjectEnergyConsumedInfoListResponse,
    ProjectEnergyExportedInfoListResponse,
    ProjectProductionInfoListResponse,
    ProjectSelfconsumptionInfoListResponse,
    QueryParams,
)
from ..utils import api_info, list_response, single_response


class EnergyCommunityApiService(Component):
    _inherit = ["base.rest.service", "api.service.utils"]
    _name = "energy_community.api.service"
    _collection = "energy_communities.api.services"
    _usage = "community"
    _description = """
        Set of enpoints that retrieve and manage information about energy communities
    """
    _work_on_model = "res.company"

    def __init__(self, *args):
        super().__init__(*args)

    def check_service(self, community_id, service_id):
        with api_info(
            self.env,
            self._work_on_model,
            CommunityServiceInfo,
            community_id,
        ) as component:
            service = component._get_project(community_id, service_id)
            if not service:
                raise MissingError(f"Community service with id {service_id} not found")
        return True

    @restapi.method(
        [(["/"], "GET")],
        output_param=PydanticModel(EnergyCommunityInfoResponse),
    )
    def energy_community(self):
        """
        Basic information about a energy community
        """
        self._validate_headers()
        community_id = int(request.httprequest.headers.get("CommunityId"))
        with api_info(
            self.env,
            self._work_on_model,
            EnergyCommunityInfo,
            community_id,
        ) as component:
            community_info = component.get_energy_community_info(community_id)
        return single_response(request, EnergyCommunityInfoResponse, community_info)

    @restapi.method(
        [(["/community_services"], "GET")],
        input_param=PydanticModel(QueryParams),
        output_param=PydanticModel(CommunityServiceInfoListResponse),
    )
    def energy_community_community_services_info(self, query_params: QueryParams):
        """
        Set of services that offer an energy community
        """
        self._validate_headers()
        community_id = int(request.httprequest.headers.get("CommunityId"))
        paging = self._get_pagination_limits(query_params)
        with api_info(
            self.env,
            self._work_on_model,
            CommunityServiceInfo,
            community_id,
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

    @restapi.method(
        [(["/community_services/<int:service_id>"], "GET")],
        input_param=PydanticModel(QueryParams),
        output_param=PydanticModel(CommunityServiceInfoResponse),
    )
    def energy_community_community_services_detail_info(
        self, service_id: int, query_params: QueryParams
    ):
        """
        Detailed information about a communty services of an energy community
        """
        self._validate_headers()
        community_id = int(request.httprequest.headers.get("CommunityId"))
        self.check_service(community_id, service_id)
        paging = self._get_pagination_limits(query_params)
        with api_info(
            self.env,
            self._work_on_model,
            CommunityServiceInfo,
            community_id,
            paging=paging,
        ) as component:
            community_service = component.community_service_detail(
                community_id, service_id
            )
        return single_response(
            request,
            CommunityServiceInfoResponse,
            community_service,
        )

    @restapi.method(
        [(["/community_services/metrics"], "GET")],
        input_param=PydanticModel(QueryParams),
        output_param=PydanticModel(CommunityServiceMetricsInfoListResponse),
    )
    def community_services_metrics_info(self, query_params: QueryParams):
        self._validate_headers()
        community_id = int(request.httprequest.headers.get("CommunityId"))
        paging = self._get_pagination_limits(query_params)
        date_from, date_to = self._get_dates_range(query_params)
        with api_info(
            self.env,
            self._work_on_model,
            CommunityServiceMetricsInfo,
            community_id=community_id,
            paging=paging,
        ) as component:
            total_community_services = component.total_community_services(community_id)
            community_service_metrics = component.get_community_services_metrics(
                community_id, date_from, date_to
            )
        return list_response(
            request,
            CommunityServiceMetricsInfoListResponse,
            community_service_metrics,
            total_community_services,
            paging,
        )

    @restapi.method(
        [(["/community_services/<int:service_id>/metrics"], "GET")],
        input_param=PydanticModel(QueryParams),
        output_param=PydanticModel(CommunityServiceMetricsInfoResponse),
    )
    def community_service_metrics_info(
        self, service_id: int, query_params: QueryParams
    ):
        self._validate_headers()
        community_id = int(request.httprequest.headers.get("CommunityId"))
        self.check_service(community_id, service_id)
        date_from, date_to = self._get_dates_range(query_params)
        with api_info(
            self.env,
            self._work_on_model,
            CommunityServiceMetricsInfo,
            community_id=community_id,
        ) as component:
            community_service_metrics = component.get_community_service_metrics(
                community_id, service_id, date_from, date_to
            )
        return single_response(
            request,
            CommunityServiceMetricsInfoResponse,
            community_service_metrics,
        )

    @restapi.method(
        [(["/community_services/<int:service_id>/metrics/energy_production"], "GET")],
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
            daily_production = component.get_project_daily_production(
                project, date_from, date_to
            )
        return list_response(
            request,
            ProjectProductionInfoListResponse,
            daily_production,
            len(daily_production),
            paging,
        )

    @restapi.method(
        [
            (
                ["/community_services/<int:service_id>/metrics/energy_selfconsumption"],
                "GET",
            )
        ],
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
            daily_selfconsumption = component.get_project_daily_selfconsumption(
                project, date_from, date_to
            )
        return list_response(
            request,
            ProjectProductionInfoListResponse,
            daily_selfconsumption,
            len(daily_selfconsumption),
            paging,
        )

    @restapi.method(
        [(["/community_services/<int:service_id>/metrics/energy_exported"], "GET")],
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
            daily_selfconsumption = component.get_project_daily_exported_energy(
                project, date_from, date_to
            )
        return list_response(
            request,
            ProjectEnergyExportedInfoListResponse,
            daily_selfconsumption,
            len(daily_selfconsumption),
            paging,
        )

    @restapi.method(
        [(["/community_services/<int:service_id>/metrics/energy_consumption"], "GET")],
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
            daily_selfconsumption = component.get_project_daily_consumed_energy(
                project, date_from, date_to
            )
        return list_response(
            request,
            ProjectEnergyConsumedInfoListResponse,
            daily_selfconsumption,
            len(daily_selfconsumption),
            paging,
        )
