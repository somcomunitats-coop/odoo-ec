from typing import List

from odoo.addons.component.core import Component

from ..schemas import (
    CommunityServiceMetricsInfo,
    EnergyPoint,
    MetricInfo,
    UnitEnum,
)


class ProjectMetricsApiInfo(Component):
    _name = "project.metrics.api.info"
    _inherit = "api.info"
    _usage = "metrics.info"

    def get_project_metrics(
        self, project, partner, date_from, date_to
    ) -> CommunityServiceMetricsInfo:
        monitoring_service = project.monitoring_service()
        if not monitoring_service:
            return {}
        member_contract = project.contract_ids.filtered(
            lambda contract: contract.partner_id == partner
        )
        service_parameters = {
            "system_id": project.selfconsumption_id.code,
            "member_id": member_contract.code,
            "date_from": date_from,
            "date_to": date_to,
        }
        metrics_info = CommunityServiceMetricsInfo(
            id=project.id,
            name=project.name,
            type="fotovoltaic",
            shares=MetricInfo(
                value=member_contract.supply_point_assignation_id.coefficient,
                unit=UnitEnum.percentage,
            ),
            energy_shares=MetricInfo(
                value=member_contract.supply_point_assignation_id.energy_shares,
                unit=UnitEnum.kwn,
            ),
            energy_production=MetricInfo(
                value=monitoring_service.energy_production_by_member(
                    **service_parameters
                ),
                unit=UnitEnum.kwh,
            ),
            energy_consumption=MetricInfo(
                value=monitoring_service.energy_consumption_by_member(
                    **service_parameters
                ),
                unit=UnitEnum.kwh,
            ),
            selfproduction_ratio=MetricInfo(
                value=monitoring_service.energy_selfconsumption_ratio_by_member(
                    **service_parameters
                ),
                unit=UnitEnum.percentage,
            ),
            surplus_ratio=MetricInfo(
                value=monitoring_service.energy_surplus_ratio_by_member(
                    **service_parameters
                ),
                unit=UnitEnum.percentage,
            ),
            gridconsumption_ratio=MetricInfo(
                value=monitoring_service.energy_usage_ratio_from_grid_by_member(
                    **service_parameters
                ),
                unit=UnitEnum.percentage,
            ),
            selfconsumption_ratio=MetricInfo(
                value=monitoring_service.energy_usage_ratio_from_selfconsumption_by_member(
                    **service_parameters
                ),
                unit=UnitEnum.percentage,
            ),
            environment_saves=MetricInfo(
                value=monitoring_service.co2save_by_member(**service_parameters),
                unit=UnitEnum.grco2,
            ),
        )
        return metrics_info


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
            daily_production = monitoring_service.daily_production_by_member(
                system_id=project.selfconsumption_id.code,
                member_id=member_contract.code,
                date_from=date_from,
                date_to=date_to,
            )
            return [EnergyPoint(**point._asdict()) for point in daily_production]
        return []

    def get_project_from_service(self, service_id):
        project = self.env[self._apply_on].browse(service_id)
        if project.exists():
            return project

    def get_project_daily_selfconsumption(
        self, project, partner, date_from, date_to
    ) -> List[EnergyPoint]:
        monitoring_service = project.monitoring_service()
        if monitoring_service:
            member_contract = project.contract_ids.filtered(
                lambda contract: contract.partner_id == partner
            )
            daily_selfconsumption = monitoring_service.daily_selfconsumption_by_member(
                system_id=project.selfconsumption_id.code,
                member_id=member_contract.code,
                date_from=date_from,
                date_to=date_to,
            )
            return [EnergyPoint(**point._asdict()) for point in daily_selfconsumption]
        return []

    def get_project_daily_exported_energy(
        self, project, partner, date_from, date_to
    ) -> List[EnergyPoint]:
        monitoring_service = project.monitoring_service()
        if monitoring_service:
            member_contract = project.contract_ids.filtered(
                lambda contract: contract.partner_id == partner
            )
            daily_exported_energy = monitoring_service.daily_gridinjection_by_member(
                system_id=project.selfconsumption_id.code,
                member_id=member_contract.code,
                date_from=date_from,
                date_to=date_to,
            )
            return [EnergyPoint(**point._asdict()) for point in daily_exported_energy]
        return []

    def get_project_daily_consumed_energy(
        self, project, partner, date_from, date_to
    ) -> List[EnergyPoint]:
        monitoring_service = project.monitoring_service()
        if monitoring_service:
            member_contract = project.contract_ids.filtered(
                lambda contract: contract.partner_id == partner
            )
            daily_consumed_energy = monitoring_service.daily_consumption_by_member(
                system_id=project.selfconsumption_id.code,
                member_id=member_contract.code,
                date_from=date_from,
                date_to=date_to,
            )
            return [EnergyPoint(**point._asdict()) for point in daily_consumed_energy]
        return []
