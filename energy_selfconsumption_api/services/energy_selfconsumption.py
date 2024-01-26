from typing import List

from odoo.api import Environment

from odoo.addons.base.models.res_users import Users

from ..schemas import SelfConsumptionProjectInfo


class EnergySelfconsumptionService:
    def __init__(self, env: Environment, user: Users) -> None:
        self.model = env["energy_selfconsumption.selfconsumption"].with_user(user)

    def selfconsumption_projects(
        self,
        project_code: str = None,
        limit: int = None,
        offset: int = None,
    ) -> List[SelfConsumptionProjectInfo]:
        search_domain = bool(project_code) and [("code", "=", project_code)] or []
        return [
            SelfConsumptionProjectInfo(
                project_code=project.code,
                project_name=project.name,
                energy_community_id=project.project_id.id,
                energy_community_name=project.company_id.name,
                power=project.power,
            )
            for project in self.model.search(search_domain, limit=limit, offset=offset)
        ]

    @property
    def total_selfconsumption_projects(self) -> int:
        return self.model.search_count([])
