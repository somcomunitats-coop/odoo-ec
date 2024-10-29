from odoo.exceptions import MissingError
from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import Component

from ..components import ProjectNotFoundException
from ..schemas import (
    DEFAULT_PAGE_SIZE,
    PaginationLimits,
    PagingParam,
    ProjectInfoListResponse,
    ProjectInfoResponse,
    SelfConsumptionProjectInfo,
    SelfConsumptionProjectMember,
    SelfConsumptionProjectMemberListResponse,
)
from ..utils import api_info, list_response, single_response


class EnergyProjectApiService(Component):
    _inherit = ["base.rest.service", "api.service.utils"]
    _name = "energy_project.service"
    _collection = "energyselfconsumption.api.services"
    _usage = "projects"
    _description = """
    Energy selfconsumption API Services
    This service implements the necessary endpoints for energy providers to
    get information about the projects that they manage.
    """

    _work_on_model = "energy_selfconsumption.selfconsumption"

    @restapi.method(
        [(["/"], "GET")],
        input_param=PydanticModel(PagingParam),
        output_param=PydanticModel(ProjectInfoListResponse),
    )
    def get_selfconsumption_projects(self, paging_param):
        paging = self._get_pagination_limits(paging_param)
        with api_info(
            self.env, self._work_on_model, SelfConsumptionProjectInfo, paging=paging
        ) as component:
            total_projects = component.total_selfconsumption_projects
            projects = component.selfconsumption_projects()
        return list_response(
            request, ProjectInfoListResponse, projects, total_projects, paging
        )

    @restapi.method(
        [(["/<string:project_code>"], "GET")],
        output_param=PydanticModel(ProjectInfoResponse),
    )
    def get_selfconsumption_project_by_code(
        self, project_code: str
    ) -> ProjectInfoResponse:
        with api_info(
            self.env, self._work_on_model, SelfConsumptionProjectInfo
        ) as component:
            projects = component.selfconsumption_projects(project_code)

        project = projects[0] if projects and len(projects) > 0 else None
        if not project:
            raise MissingError(f"Project {project_code} not found")
        return single_response(request, ProjectInfoResponse, project)

    @restapi.method(
        [
            (
                [
                    "/<string:project_code>/members",
                ],
                "GET",
            )
        ],
        input_param=PydanticModel(PagingParam),
        output_param=PydanticModel(SelfConsumptionProjectMemberListResponse),
    )
    def selfconsumption_project_members(
        self,
        project_code: str,
        paging_param: PagingParam,
    ) -> SelfConsumptionProjectMemberListResponse:
        paging = self._get_pagination_limits(paging_param)
        with api_info(
            self.env, self._work_on_model, SelfConsumptionProjectMember, paging=paging
        ) as component:
            try:
                members = component.selfconsumption_project_members(project_code)
                total_projectmembers = component.total_project_members(project_code)
            except ProjectNotFoundException as e:
                raise MissingError(str(e))
            else:
                return list_response(
                    request,
                    SelfConsumptionProjectMemberListResponse,
                    members,
                    total_projectmembers,
                    paging,
                )
