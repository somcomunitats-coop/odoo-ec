import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from typing_extensions import Annotated

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import odoo_env

from ..dependencies import authenticated_endpoint, paging
from ..schemas import PaginationLimits
from ..schemas.responses import (
    ProjectsInfoListResponse,
    SingleProjectInfoResponse,
)
from ..services import EnergySelfconsumptionService
from ..utils import make_list_response, make_single_response

logger = logging.getLogger("__name__")

router = APIRouter(tags=["energy_selfconsumption"])


@router.get("/projects", response_model=ProjectsInfoListResponse)
def selfconsumption_projects(
    request: Request,
    env: Annotated[Environment, Depends(odoo_env)],
    auth_user: Annotated[Any, Depends(authenticated_endpoint)],
    paging: Annotated[PaginationLimits, Depends(paging)],
) -> ProjectsInfoListResponse:
    energy_selfconsumption_service = EnergySelfconsumptionService(env, auth_user)
    projects = energy_selfconsumption_service.selfconsumption_projects()
    return make_list_response(projects, request)


@router.get("/projects/{project_code}", response_model=SingleProjectInfoResponse)
def get_selfconsumption_project_by_cau(
    project_code: str,
    request: Request,
    env: Annotated[Environment, Depends(odoo_env)],
    auth_user: Annotated[Any, Depends(authenticated_endpoint)],
) -> SingleProjectInfoResponse:
    energy_selfconsumption_service = EnergySelfconsumptionService(env, auth_user)
    projects = energy_selfconsumption_service.selfconsumption_projects(project_code)
    project = projects[0] if projects and len(projects) > 0 else None

    return make_single_response(project, request)
