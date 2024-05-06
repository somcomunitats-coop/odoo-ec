from typing import List

from odoo.api import Environment

from odoo.addons.base.models.res_users import Users

from ..schemas import SelfConsumptionProjectInfo, SelfConsumptionProjectMember


class ProjectNotFoundException(Exception):
    pass


class EnergySelfconsumptionService:
    def __init__(self, env: Environment, user: Users) -> None:
        self.Selfconsumption = env["energy_selfconsumption.selfconsumption"].with_user(
            user
        )
        self.SupplyPointAssignation = env[
            "energy_selfconsumption.supply_point_assignation"
        ].with_user(user)

    @property
    def total_selfconsumption_projects(self) -> int:
        return self.Selfconsumption.search_count([])

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
            for project in self.Selfconsumption.search(
                search_domain, limit=limit, offset=offset
            )
        ]

    def _get_selfconsumption_project(self, project_code: str):
        project = self.Selfconsumption.search([("code", "=", project_code)])
        return project and project[0] or None

    def total_project_members(self, project_code: str) -> int:
        project = self._get_selfconsumption_project(project_code)
        search_domain = [
            ("selfconsumption_project_id", "=", project.id),
        ]
        return self.SupplyPointAssignation.search_count(search_domain)

    def selfconsumption_project_members(
        self,
        project_code: str,
        limit: int = None,
        offset: int = None,
    ) -> List[SelfConsumptionProjectMember]:
        project = self._get_selfconsumption_project(project_code)
        if not project:
            raise ProjectNotFoundException(f"Project {project_code} not found")

        search_domain = [
            ("selfconsumption_project_id", "=", project.id),
        ]
        return [
            SelfConsumptionProjectMember(
                supply_point_code=assignation.supply_point_id.code,
                supply_point_address=assignation.supply_point_id.street,
                supply_point_postalcode=assignation.supply_point_id.zip,
                supply_point_town=assignation.supply_point_id.city,
                supply_point_state=assignation.supply_point_id.state_id.name,
                distribution_coefficient=assignation.coefficient,
                owner_name=assignation.owner_id.firstname,
                owner_surnames=assignation.owner_id.lastname,
                owner_vat=assignation.owner_id.vat or "",
            )
            for assignation in self.SupplyPointAssignation.search(
                search_domain, limit=limit, offset=offset
            )
        ]
