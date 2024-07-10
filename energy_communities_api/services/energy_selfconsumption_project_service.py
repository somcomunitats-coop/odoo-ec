import logging

from werkzeug.exceptions import NotFound

from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import Component

from ..components import (
    EnergySelfconsumptionProjectsComponent,
    ProjectNotFoundException,
)
from ..schemas import (
    DEFAULT_PAGE_SIZE,
    PaginationLimits,
    Paging,
    ProjectMembersResponse,
    ProjectsInfoListResponse,
    SingleProjectInfoResponse,
)
from ..utils import collection_response, single_response

logger = logging.getLogger("__name__")


class EnergyProjectApiService(Component):
    _inherit = "base.rest.service"
    _name = "energy_project.service"
    _collection = "energyselfconsumption.api.services"
    _usage = "projects"
    _description = """
    Energy selfconsumption API Services
    This service implements the necessary endpoints for energy providers to
    get information about the projects that they manage.
    """

    @restapi.method(
        [(["/"], "GET")],
        inpunt_param=PydanticModel(Paging),
        output_param=PydanticModel(ProjectsInfoListResponse),
    )
    def get_selfconsumption_projects(self, selfconsumption_paging_param):
        page = selfconsumption_paging_param.page or 1
        page_size = selfconsumption_paging_param.size_page or DEFAULT_PAGE_SIZE

        energy_selfconsumption_service = EnergySelfconsumptionProjectsComponent(
            env=request.env, user=request.uid
        )
        paging = PaginationLimits(
            limit=page_size, offset=(page - 1) * page_size, page=page
        )
        total_projects = energy_selfconsumption_service.total_selfconsumption_projects
        projects = energy_selfconsumption_service.selfconsumption_projects(
            limit=paging.limit, offset=paging.offset
        )
        return collection_response(
            request, ProjectsInfoListResponse, projects, total_projects, paging
        )

    @restapi.method(
        [(["/<string:project_code>"], "GET")],
        output_param=PydanticModel(SingleProjectInfoResponse),
    )
    def get_selfconsumption_project_by_code(
        project_code: str,
    ) -> SingleProjectInfoResponse:
        energy_selfconsumption_service = EnergySelfconsumptionProjectsComponent(
            env=request.env, user=request.uid
        )
        projects = energy_selfconsumption_service.selfconsumption_projects(project_code)
        project = projects[0] if projects and len(projects) > 0 else None
        if not project:
            raise NotFound(f"Project {project_code} not found")
        return single_response(request, SingleProjectInfoResponse, project)

    @restapi.method(
        [
            (
                [
                    "/<string:project_code>/members",
                ],
                "GET",
            )
        ],
        inpunt_param=PydanticModel(Paging),
        output_param=PydanticModel(ProjectMembersResponse),
    )
    def selfconsumption_project_members(
        selfconsumption_paging_param,
        _project_code: str,
    ) -> ProjectMembersResponse:
        page = selfconsumption_paging_param.page or 1
        page_size = selfconsumption_paging_param.size_page or DEFAULT_PAGE_SIZE

        energy_selfconsumption_service = EnergySelfconsumptionProjectsComponent(
            env=request.env, user=request.uid
        )
        paging = PaginationLimits(
            limit=page_size, offset=(page - 1) * page_size, page=page
        )
        try:
            members = energy_selfconsumption_service.selfconsumption_project_members(
                _project_code, limit=paging.limit, offset=paging.offset
            )
            total_projectmembers = energy_selfconsumption_service.total_project_members(
                _project_code
            )
        except ProjectNotFoundException as e:
            raise NotFound(str(e))
        else:
            return collection_response(
                request, ProjectMembersResponse, members, total_projectmembers, paging
            )
