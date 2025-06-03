from datetime import date
from typing import List

from odoo.exceptions import MissingError

from odoo.addons.component.core import Component
from odoo.addons.energy_project.models.project import DRAFT
from odoo.addons.energy_selfconsumption.models.selfconsumption import ACTIVE

from ..schemas import (
    Address,
    CommunityServiceInfo,
    CommunityServiceMetricsInfo,
    EnergyCommunityInfo,
)


class EnergyCommunityApiInfo(Component):
    _name = "energy_community.api.info"
    _inherit = "api.info"
    _usage = "api.info"
    _apply_on = "res.company"

    _communities_services_domain = lambda _, community_id: [
        ("company_id", "=", community_id),
        ("state", "!=", DRAFT),
    ]

    _community_service_domain = lambda _, community_id, service_id: [
        ("company_id", "=", community_id),
        ("id", "=", service_id),
        ("state", "!=", DRAFT),
    ]

    def get_energy_community_info(self, community_id) -> EnergyCommunityInfo:
        community = self.env[self._apply_on].search([("id", "=", community_id)])
        if not community:
            raise MissingError(f"Community with id {community_id} not found")

        return self.work.schema_class(
            id=community.id,
            name=community.name,
            coordinator=community.parent_id.sudo().name,
            members=len(community.get_ce_members()),
            services=community.sudo().get_all_energy_actions_dict_list(),
            image=community.logo,
            landing_photo=community.landing_page_id.sudo().primary_image_file,
            social={
                "email": community.email,
                "web": community.website,
                "twitter": community.social_twitter or None,
                "instagram": community.social_instagram or None,
                "telegram": community.social_telegram or None,
                "facebook": community.social_facebook or None,
            },
        )

    def total_community_services(self, community_id: int) -> int:
        domain = self._communities_services_domain(community_id)
        return self.env["energy_selfconsumption.selfconsumption"].search_count(domain)

    def get_community_services(self, community_id: int) -> List[CommunityServiceInfo]:
        community_services = []
        community_projects = self._get_projects(community_id)
        for service in community_projects:
            service_info = self._community_service_info(service)
            community_services += [service_info]
        return community_services

    def community_service_detail(
        self, community_id: int, service_id: int
    ) -> CommunityServiceInfo:
        community_service = self._get_project(community_id, service_id)
        return self._community_service_info(community_service)

    def get_community_services_metrics(
        self, community_id: int, date_from: date, date_to: date
    ) -> List[CommunityServiceMetricsInfo]:
        metrics = []
        metrics_component = self.component(usage="metrics.info")
        community_projects = self._get_projects(community_id)
        for project in community_projects:
            metrics_info = metrics_component.get_project_metrics(
                project, date_from, date_to
            )
            if metrics_info:
                metrics += [metrics_info]
        return metrics

    def get_community_service_metrics(
        self, community_id: int, service_id: int, date_from: date, date_to: date
    ) -> CommunityServiceMetricsInfo:
        project = self._get_project(community_id, service_id)
        if not project:
            raise MissingError(f"Community service with id {service_id} not found")
        metrics_component = self.component(usage="metrics.info")
        return metrics_component.get_project_metrics(project, date_from, date_to)

    def _get_projects(self, community_id: int):
        domain = self._communities_services_domain(community_id)
        if self.work.paging:
            return self.env["energy_selfconsumption.selfconsumption"].search(
                domain, limit=self.work.paging.limit, offset=self.work.paging.offset
            )
        return self.env["energy_selfconsumption.selfconsumption"].search(domain)

    def _get_project(self, community_id, service_id: int):
        domain = self._community_service_domain(community_id, service_id)
        return self.env["energy_selfconsumption.selfconsumption"].search(domain)

    def _community_service_info(self, service) -> CommunityServiceInfo:
        service_info = CommunityServiceInfo(
            id=service.id,
            type="fotovoltaic",
            name=service.name,
            status=service.state,
            has_monitoring=service.project_id.monitoring_service() is not None,
            open_inscriptions=service.conf_state == ACTIVE,
            inscriptions=len(service.inscription_ids),
            inscriptions_url_form=service.conf_state == ACTIVE
            and service.conf_url_form
            or "",
            address=Address(
                street=service.street,
                street2=service.street2 or "",
                postal_code=service.zip,
                city=service.city,
                state=service.state_id.name,
                country=service.country_id.name,
            ),
            power=service.power,
        )
        return service_info
