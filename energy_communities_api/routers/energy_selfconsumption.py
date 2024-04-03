import logging

from fastapi import APIRouter, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND

from ..dependencies import EnergySelfconsumptionDependency, PagingDependency
from ..schemas.responses import (
    ProjectMembersResponse,
    ProjectsInfoListResponse,
    SingleProjectInfoResponse,
)
from ..services import ProjectNotFoundException
from ..utils import collection_response, single_response

logger = logging.getLogger("__name__")

router = APIRouter(tags=["energy_selfconsumption"])


@router.get(
    "/projects",
    response_model=ProjectsInfoListResponse,
    name="selfconsumption_projects",
)
async def selfconsumption_projects(
    request: Request,
    paging: PagingDependency,
    energy_selfconsumption_service: EnergySelfconsumptionDependency,
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
async def get_selfconsumption_project_by_code(
    project_code: str,
    request: Request,
    energy_selfconsumption_service: EnergySelfconsumptionDependency,
) -> SingleProjectInfoResponse:
    projects = energy_selfconsumption_service.selfconsumption_projects(project_code)
    project = projects[0] if projects and len(projects) > 0 else None
    if not project:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"Project {project_code} not found"
        )
    return single_response(request, SingleProjectInfoResponse, project)


@router.get(
    "/projects/{project_code}/members",
    response_model=ProjectMembersResponse,
    name="selfconsumption_project_members",
)
async def selfconsumption_project_members(
    project_code: str,
    request: Request,
    paging: PagingDependency,
    energy_selfconsumption_service: EnergySelfconsumptionDependency,
) -> ProjectMembersResponse:
    try:
        members = energy_selfconsumption_service.selfconsumption_project_members(
            project_code, limit=paging.limit, offset=paging.offset
        )
        total_projectmembers = energy_selfconsumption_service.total_project_members(
            project_code
        )
    except ProjectNotFoundException as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
    else:
        return collection_response(
            request, ProjectMembersResponse, members, total_projectmembers, paging
        )
