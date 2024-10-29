from typing import List

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
            projects = self.env_model.search(
                search_domain,
                limit=self.work.paging.limit,
                offset=self.work.paging.offset,
            )
        else:
            projects = self.env_model.search(search_domain)
        if projects:
            return self.get_list(projects)
        return []

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
            project_members = self.env[
                "energy_selfconsumption.supply_point_assignation"
            ].search(
                search_domain,
                limit=self.work.paging.limit,
                offset=self.work.paging.offset,
            )
        else:
            project_members = self.env[
                "energy_selfconsumption.supply_point_assignation"
            ].search(search_domain)
        if project_members:
            return self.get_list(project_members)
        return []
