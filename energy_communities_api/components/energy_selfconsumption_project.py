from typing import List

from odoo.api import Environment

from odoo.addons.base.models.res_users import Users
from odoo.addons.component.core import Component

from ..schemas import SelfConsumptionProjectInfo, SelfConsumptionProjectMember


class ProjectNotFoundException(Exception):
    pass


class EnergySelfconsumptionApiInfo(Component):
    _name = "energy_selfconsumption.api.info"
    _inherit = "api.info"
    _usage = "api.info"
    _apply_on = "energy_selfconsumption.selfconsumption"

    def __init__(self, *args):
        super().__init__(*args)
        self.env_model = self.env[self._apply_on]

    @property
    def total_selfconsumption_projects(self) -> int:
        return self.env_model.search_count([])

    def selfconsumption_projects(
        self,
        project_code: str = None,
    ) -> List[SelfConsumptionProjectInfo]:
        search_domain = bool(project_code) and [("code", "=", project_code)] or []
        if self.work.paging:
            search_results = self.env_model.search(
                search_domain,
                limit=self.work.paging.limit,
                offset=self.work.paging.offset,
            )
        else:
            search_results = self.env_model.search(search_domain)
        return [
            SelfConsumptionProjectInfo(
                project_code=project.code,
                project_name=project.name,
                energy_community_id=project.project_id.id,
                energy_community_name=project.company_id.name,
                power=project.power,
            )
            for project in search_results
        ]

    def _get_selfconsumption_project(self, project_code: str):
        project = self.env_model.search([("code", "=", project_code)])
        return project and project[0] or None

    def total_project_members(self, project_code: str) -> int:
        project = self._get_selfconsumption_project(project_code)
        search_domain = [
            ("selfconsumption_project_id", "=", project.id),
        ]
        return self.env["energy_selfconsumption.supply_point_assignation"].search_count(
            search_domain
        )

    def selfconsumption_project_members(
        self,
        project_code: str,
    ) -> List[SelfConsumptionProjectMember]:
        project = self._get_selfconsumption_project(project_code)
        if not project:
            raise ProjectNotFoundException(f"Project {project_code} not found")
        search_domain = [
            ("selfconsumption_project_id", "=", project.id),
        ]
        if self.work.paging:
            search_results = self.env[
                "energy_selfconsumption.supply_point_assignation"
            ].search(
                search_domain,
                limit=self.work.paging.limit,
                offset=self.work.paging.offset,
            )
        else:
            search_results = self.env[
                "energy_selfconsumption.supply_point_assignation"
            ].search(search_domain)
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
            for assignation in search_results
        ]
