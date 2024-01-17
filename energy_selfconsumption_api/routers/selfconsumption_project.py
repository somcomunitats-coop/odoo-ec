import sys

if sys.version_info >= (3, 9):
    from typing import Annotated, List
else:
    from typing_extensions import Annotated, List

from fastapi import APIRouter, Depends

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import odoo_env

from ..domain import get_selfconsumption_projects
from ..schemas.responses import (
    ProjectsInfoListResponse,
    SingleProjectInfoResponse,
)
from ..utils import make_list_response, make_single_response

router = APIRouter(tags=["energy_selfconsumption"])


@router.get("/projects", response_model=ProjectsInfoListResponse)
def selfconsumption_projects(
    env: Annotated[Environment, Depends(odoo_env)]
) -> ProjectsInfoListResponse:
    projects = get_selfconsumption_projects(env, cau=None)

    return make_list_response(projects)


@router.get("/projects/{project_code}", response_model=SingleProjectInfoResponse)
def get_selfconsumption_project_by_cau(
    project_code: str,
) -> SingleProjectInfoResponse:
    projects = get_selfconsumption_projects(env, project_code)
    project = projects[0] if projects and len(projects) > 0 else None

    return make_single_response(project)
