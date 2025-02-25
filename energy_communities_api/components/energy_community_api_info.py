from typing import List

from odoo.exceptions import MissingError

from odoo.addons.component.core import Component
from odoo.addons.energy_project.models import DRAFT

from ..schemas import CommunityServiceInfo, EnergyCommunityInfo


class EnergyCommunityApiInfo(Component):
    _name = "energy_community.api.info"
    _inherit = "api.info"
    _usage = "api.info"
    _apply_on = "res.company"

    _communities_services_domain = lambda _, community_id: [
        ("company_id", "=", community_id),
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
            services=community.sudo().get_energy_actions_dict_list(),
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

    def get_community_services(self, community_id: str) -> List[CommunityServiceInfo]:
        community_services = []
        domain = self._communities_services_domain(community_id)
        community_services = self.env["energy_project.project"].search(domain)
        for service in community_services:
            service_info = CommunityServiceInfo(
                id=service.id,
                type="fotovoltaic",
                name=service.name,
                status=service.state,
                inscriptions=len(service.inscription_ids),
                address=service.full_address,
            )
            community_services += [service_info]
        return community_services
