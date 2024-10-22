from odoo.exceptions import MissingError

from odoo.addons.component.core import Component

from ..schemas import EnergyCommunityInfo


class EnergyCommunityApiInfo(Component):
    _name = "energy_community.api.info"
    _inherit = "api.info"
    _usage = "api.info"
    _apply_on = "res.company"

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
