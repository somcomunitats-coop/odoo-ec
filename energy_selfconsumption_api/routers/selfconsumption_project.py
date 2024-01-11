import sys

if sys.version_info >= (3, 9):
    from typing import Annotated, List
else:
    from typing_extensions import Annotated, List

from fastapi import APIRouter, Depends

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import odoo_env

from ..domain import get_selfconsumption_projects
from ..schemas import SelfConsumptionProjectInfo

router = APIRouter(tags=["energy_selfconsumption"])


@router.get("/projects", response_model=List[SelfConsumptionProjectInfo])
def selfconsumption_projects(
    env: Annotated[Environment, Depends(odoo_env)]
) -> List[SelfConsumptionProjectInfo]:
    return get_selfconsumption_projects(env, cau=None)


@router.get("/projects/{cau}", response_model=List[SelfConsumptionProjectInfo])
def get_selfconsumption_project_by_cau(
    cau: str, env: Annotated[Environment, Depends(odoo_env)]
) -> List[SelfConsumptionProjectInfo]:
    return get_selfconsumption_projects(env, cau)
