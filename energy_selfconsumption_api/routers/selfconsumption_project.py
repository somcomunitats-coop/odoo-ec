import logging

from fastapi import APIRouter, Depends, Request
from typing_extensions import Annotated

from ..dependencies import energy_selfconsumption_service, paging
from ..schemas import PaginationLimits
from ..schemas.responses import (
    ProjectsInfoListResponse,
    SingleProjectInfoResponse,
)
from ..services import EnergySelfconsumptionService
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
    paging: Annotated[PaginationLimits, Depends(paging)],
    energy_selfconsumption_service: Annotated[
        EnergySelfconsumptionService, Depends(energy_selfconsumption_service)
    ],
) -> ProjectsInfoListResponse:
    total_projects = energy_selfconsumption_service.total_selfconsumption_projects
    projects = energy_selfconsumption_service.selfconsumption_projects(
        limit=paging.limit, offset=paging.offset
    )

    return collection_response(request, projects, total_projects, paging)


@router.get(
    "/projects/{project_code}",
    response_model=SingleProjectInfoResponse,
    name="selfconsumption_project_by_code",
)
def get_selfconsumption_project_by_code(
    project_code: str,
    request: Request,
    energy_selfconsumption_service: Annotated[
        EnergySelfconsumptionService, Depends(energy_selfconsumption_service)
    ],
) -> SingleProjectInfoResponse:
    projects = energy_selfconsumption_service.selfconsumption_projects(project_code)
    project = projects[0] if projects and len(projects) > 0 else None

    return make_single_response(project, request)
