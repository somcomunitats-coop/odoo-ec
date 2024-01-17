import sys

if sys.version_info >= (3, 9):
    from typing import Annotated, List
else:
    from typing_extensions import Annotated, List

import logging

from fastapi import APIRouter, Depends

from odoo.api import Environment

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import authenticated_partner, odoo_env

from ..dependencies import AuthHeader
from ..domain import get_selfconsumption_projects
from ..schemas.responses import (
    ProjectsInfoListResponse,
    SingleProjectInfoResponse,
)
from ..utils import make_list_response, make_single_response

logger = logging.getLogger("__name__")

router = APIRouter(tags=["energy_selfconsumption"])


@router.get("/projects", response_model=ProjectsInfoListResponse)
def selfconsumption_projects(
    env: Annotated[Environment, Depends(odoo_env)],
    api_key: Annotated[str, Depends(AuthHeader)],
    partner: Annotated[Partner, Depends(authenticated_partner)],
) -> ProjectsInfoListResponse:
    logger.debug("EEEPP partner %s buscant projectes", partner.name)
    projects = get_selfconsumption_projects(env, cau=None)

    return make_list_response(projects)


@router.get("/projects/{project_code}", response_model=SingleProjectInfoResponse)
def get_selfconsumption_project_by_cau(
    project_code: str,
    env: Annotated[Environment, Depends(odoo_env)],
    api_key: Annotated[str, Depends(AuthHeader)],
    partner: Annotated[Partner, Depends(authenticated_partner)],
) -> SingleProjectInfoResponse:
    projects = get_selfconsumption_projects(env, project_code)
    project = projects[0] if projects and len(projects) > 0 else None

    return make_single_response(project)
