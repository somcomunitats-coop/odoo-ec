
import logging
from odoo.addons.component.core import Component
from . import schemas

_logger = logging.getLogger(__name__)


class LandingService(Component):
    _inherit = "base.rest.private_abstract_service"
    _name = "ce.landing.service"
    _usage = "landing"
    _description = """
        CE WP landing page requests
    """

    # TODO: This is not restful, we should ask for landing_id directly. Refactor WP before fixing this.
    def get(self, _id):
        related_company = self.env['res.company'].browse(_id)
        return self._to_dict(related_company.landing_page_id)

    @staticmethod
    def _to_dict(landing_page):
        # TODO: move this method to model method?
        # return landing.to_dict()
        return {
            "landing": {
                "id": landing_page.id,
                "name": landing_page.name,
                "company_id": landing_page.company_id.id,
                "wp_landing_page_id": landing_page.wp_landing_page_id,
                "status": landing_page.status,
                "allow_new_members": landing_page.allow_new_members,
                "number_of_members": landing_page.number_of_members,
                "virtual_office_link": landing_page.virtual_office_link or "",
                "external_website_link": landing_page.external_website_link or "",
                "community_active_services": landing_page.company_id.get_active_services(),
                "group_image_link": landing_page.group_image_link or "",
                "short_description": landing_page.short_description or "",
                "long_description": landing_page.long_description or "",
                "why_become_cooperator": landing_page.why_become_cooperator or "",
                "become_cooperator_process": landing_page.become_cooperator_process or "",
                "subscription_information": landing_page.subscription_information or "",
                "new_cooperator_form_link": landing_page.new_cooperator_form_link or "",
                "contact_form": landing_page.contact_form or "",
                "subscription_link": landing_page.subscription_link or "",
                "social_media_link": landing_page.social_media_link or "",
                "map_geolocation": landing_page.map_geolocation or "",
                "street": landing_page.street or "",
                "postal_code": landing_page.postal_code or "",
                "city": landing_page.city or ""
            }
        }

    def _validator_get(self):
        return {}

    def _validator_return_get(self):
        return schemas.S_LANDING_PAGE_CREATE
