from typing import List

from odoo.addons.component.core import Component

from ..schemas import EnergyPoint


class ProjectApiInfo(Component):
    _name = "project.api.info"
    _inherit = "api.info"
    _usage = "api.info"
    _apply_on = "energy_project.project"

    def get_project_daily_production(
        self, project, partner, date_from, date_to
    ) -> List[EnergyPoint]:
        monitoring_service = project.monitoring_service()
        if monitoring_service:
            member_contract = project.contract_ids.filtered(
                lambda contract: contract.partner_id == partner
            )
            daily_production = monitoring_service.daily_generated_energy_by_member(
                system_id=project.selfconsumption_id.code,
                member_id=member_contract.code,
                date_from=date_from,
                date_to=date_to,
            )
            return [EnergyPoint(**point._asdict()) for point in daily_production]
        return []

    def get_project_from_service(self, service_id):
        return self.env[self._apply_on].browse(service_id)
