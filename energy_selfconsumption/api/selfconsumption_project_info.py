import sys

if sys.version_info >= (3, 9):
    from typing import Annotated, List
else:
    from typing_extensions import Annotated, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from odoo import fields, models
from odoo.api import Environment

from odoo.addons.fastapi.dependencies import odoo_env


class EnergySelfConsumptionAPI(models.Model):
    API_NAME = "ce_selfconsumption_api"

    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[(API_NAME, "Energy selfconsumption api app")],
        ondelete={API_NAME: "cascade"},
    )

    def _get_fastapi_routers(self):
        if self.app == self.API_NAME:
            return [ce_selfconsumption_api_router]
        return super()._get_fastapi_routers()


ce_selfconsumption_api_router = APIRouter()


class SelfConsumptionProjectInfo(BaseModel):
    cau: str
    project_name: str
    ce_id: str
    ce_name: str
    # d'on surt aquests state????
    # state: int
    power: float


@ce_selfconsumption_api_router.get(
    "/self-consumption", response_model=List[SelfConsumptionProjectInfo]
)
def get_selfconsumption_project_info(
    env: Annotated[Environment, Depends(odoo_env)]
) -> List[SelfConsumptionProjectInfo]:
    return [
        SelfConsumptionProjectInfo(
            cau=project.code,
            project_name=project.name,
            ce_id=project.project_id,
            ce_name=project.company_id.name,
            power=project.power,
        )
        for project in env["energy_selfconsumption.selfconsumption"].search([])
    ]
