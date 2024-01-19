import sys

if sys.version_info >= (3, 9):
    from typing import Any, List
else:
    from typing_extensions import Any, Annotated, List

from odoo.api import Environment

from ..schemas import SelfConsumptionProjectInfo


class EnergySelfconsumptionService:
    def __init__(self, env: Environment) -> None:
        self._env = env
        self.model = env["energy_selfconsumption.selfconsumption"]

    def selfconsumption_projects(
        self,
        project_code: str = None,
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
            for project in self.model.search(search_domain)
        ]
