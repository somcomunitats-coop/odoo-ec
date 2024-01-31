import logging

from fastapi import APIRouter, Request

from ..dependencies import EnergySelfconsumptionDep, PagingDep
from ..schemas.responses import (
    ProjectMembersResponse,
    ProjectsInfoListResponse,
    SingleProjectInfoResponse,
)
from ..utils import collection_response, make_single_response

logger = logging.getLogger("__name__")

router = APIRouter(tags=["energy_selfconsumption"])


@router.get(
    "/projects",
    response_model=ProjectsInfoListResponse,
    name="selfconsumption_projects",
)
def selfconsumption_projects(
    request: Request,
    paging: PagingDep,
    energy_selfconsumption_service: EnergySelfconsumptionDep,
) -> ProjectsInfoListResponse:
    total_projects = energy_selfconsumption_service.total_selfconsumption_projects
    projects = energy_selfconsumption_service.selfconsumption_projects(
        limit=paging.limit, offset=paging.offset
    )
    return collection_response(
        request, ProjectsInfoListResponse, projects, total_projects, paging
    )


@router.get(
    "/projects/{project_code}",
    response_model=SingleProjectInfoResponse,
    name="selfconsumption_project_by_code",
)
def get_selfconsumption_project_by_code(
    project_code: str,
    request: Request,
    energy_selfconsumption_service: EnergySelfconsumptionDep,
) -> SingleProjectInfoResponse:
    projects = energy_selfconsumption_service.selfconsumption_projects(project_code)
    project = projects[0] if projects and len(projects) > 0 else None
    return make_single_response(request, SingleProjectInfoResponse, project)


@router.get(
    "/projects/{project_code}/members",
    response_model=ProjectMembersResponse,
    name="selfconsumption_project_members",
)
def selfconsumption_project_members(
    project_code: str,
    request: Request,
    paging: PagingDep,
    energy_selfconsumption_service: EnergySelfconsumptionDep,
) -> ProjectMembersResponse:
    total_projectmembers = energy_selfconsumption_service.total_project_members(
        project_code
    )
    members = energy_selfconsumption_service.selfconsumption_project_members(
        project_code, limit=paging.limit, offset=paging.offset
    )
    return collection_response(
        request, ProjectMembersResponse, members, total_projectmembers, paging
    )
