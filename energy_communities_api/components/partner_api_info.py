from datetime import date
from typing import List

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.component.core import Component

from ..schemas import (
    CommunityInfo,
    CommunityServiceInfo,
    CommunityServiceMetricsInfo,
    MemberInfo,
    MetricInfo,
    UnitEnum,
)


class PartnerApiInfo(Component):
    _name = "partner.api.info"
    _inherit = "api.info"
    _usage = "api.info"
    _apply_on = "res.partner"

    _communities_domain = lambda _, partner: [
        "&",
        ("partner_id", "=", partner.id),
        "|",
        ("member", "=", True),
        ("old_member", "=", True),
    ]

    _active_communities_services_domain = lambda _, partner: [
        ("partner_id", "=", partner.id),
        ("project_id.state", "=", "active"),
    ]

    _active_community_services_domain = lambda _, service_id: [
        ("id", "=", service_id),
        ("state", "=", "active"),
    ]

    def get_member_info(self, partner: Partner) -> MemberInfo:
        return self.get(partner)

    def total_member_communities(self, partner: Partner) -> int:
        domain = self._communities_domain(partner)
        return self.env["cooperative.membership"].search_count(domain)

    def get_member_communities(self, partner: Partner) -> CommunityInfo:
        communities = self._get_communities(partner)
        if communities:
            return self.get_list(communities)
        return []

    def total_member_active_community_services(self, partner: Partner) -> int:
        domain = self._active_communities_services_domain(partner)
        return self.env["energy_project.inscription"].search_count(domain)

    def get_member_community_services(
        self, partner: Partner
    ) -> List[CommunityServiceInfo]:
        community_services = []
        domain = self._active_communities_services_domain(partner)
        registered_services = self.env["energy_project.inscription"].search(domain)
        for service in registered_services:
            member_contract = service.project_id.contract_ids.filtered(
                lambda contract: contract.partner_id == partner
            )
            service_info = CommunityServiceInfo(
                id=service.project_id.id,
                type="fotovoltaic",
                name=service.project_id.name,
                status=service.project_id.state,
                shares=member_contract.supply_point_assignation_id.coefficient,
                inscription_date=member_contract.date_start,
                inscriptions=len(service.project_id.inscription_ids),
            )
            community_services += [service_info]
        return community_services

    def get_member_community_service_detail(
        self, partner: Partner, service_id: int
    ) -> CommunityServiceInfo:
        domain = self._active_community_services_domain(service_id)
        project = self.env["energy_project.project"].search(domain)
        if project:
            member_contract = project.contract_ids.filtered(
                lambda contract: contract.partner_id == partner
            )
            return CommunityServiceInfo(
                id=project.id,
                type="fotovoltaic",
                name=project.name,
                status=project.state,
                shares=member_contract.supply_point_assignation_id.coefficient,
                inscription_date=member_contract.date_start,
                inscriptions=len(project.inscription_ids),
            )

    def get_member_community_services_metrics(
        self, partner: Partner, date_from: date, date_to: date
    ) -> List[CommunityServiceMetricsInfo]:
        metrics = []
        domain = self._active_communities_services_domain(partner)
        projects = (
            self.env["energy_project.inscription"]
            .search(domain)
            .mapped(lambda inscription: inscription.project_id)
        )
        for project in projects:
            monitoring_service = project.monitoring_service()
            if monitoring_service:
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
                    share_energy_production=MetricInfo(
                        value=monitoring_service.generated_energy_by_member(
                            **service_parameters
                        ),
                        unit=UnitEnum.kwh,
                    ),
                    selfconsumption_consumption_ratio=MetricInfo(
                        value=monitoring_service.selfconsumed_energy_ratio_by_member(
                            **service_parameters
                        ),
                        unit=UnitEnum.percentage,
                    ),
                    selfconsumption_surplus_ratio=MetricInfo(
                        value=monitoring_service.energy_surplus_ratio_by_member(
                            **service_parameters
                        ),
                        unit=UnitEnum.percentage,
                    ),
                    consumption_selfconsumption_ratio=MetricInfo(
                        value=monitoring_service.energy_usage_ratio_by_member(
                            **service_parameters
                        ),
                        unit=UnitEnum.percentage,
                    ),
                    environment_saves=MetricInfo(
                        value=monitoring_service.co2save_by_member(
                            **service_parameters
                        ),
                        unit=UnitEnum.grco2,
                    ),
                )
                metrics += [metrics_info]

        return metrics

    def get_member_community_services_metrics_by_service(
        self, partner: Partner, service_id: int, date_from: date, date_to: date
    ) -> CommunityServiceMetricsInfo:
        domain = self._active_community_services_domain(service_id)
        project = self.env["energy_project.project"].search(domain)
        if project:
            monitoring_service = project.monitoring_service()
            if monitoring_service:
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
                    share_energy_production=MetricInfo(
                        value=monitoring_service.generated_energy_by_member(
                            **service_parameters
                        ),
                        unit=UnitEnum.kwh,
                    ),
                    selfconsumption_consumption_ratio=MetricInfo(
                        value=monitoring_service.selfconsumed_energy_ratio_by_member(
                            **service_parameters
                        ),
                        unit=UnitEnum.percentage,
                    ),
                    selfconsumption_surplus_ratio=MetricInfo(
                        value=monitoring_service.energy_surplus_ratio_by_member(
                            **service_parameters
                        ),
                        unit=UnitEnum.percentage,
                    ),
                    consumption_selfconsumption_ratio=MetricInfo(
                        value=monitoring_service.energy_usage_ratio_by_member(
                            **service_parameters
                        ),
                        unit=UnitEnum.percentage,
                    ),
                    environment_saves=MetricInfo(
                        value=monitoring_service.co2save_by_member(
                            **service_parameters
                        ),
                        unit=UnitEnum.grco2,
                    ),
                )
                return metrics_info

    def _get_communities(self, partner: Partner):
        domain = self._communities_domain(partner)
        if self.work.paging:
            return (
                self.env["cooperative.membership"]
                .search(
                    domain, limit=self.work.paging.limit, offset=self.work.paging.offset
                )
                .mapped(lambda record: record.company_id)
            )
        return (
            self.env["cooperative.membership"]
            .search(domain)
            .mapped(lambda record: record.company_id)
        )
