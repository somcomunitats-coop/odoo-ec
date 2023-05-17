import logging
from odoo.addons.base_rest import restapi
from odoo.addons.component.core import Component
from odoo import _
from datetime import datetime
from . import schemas
from odoo.http import request

_logger = logging.getLogger(__name__)


class LandingService(Component):
    _inherit = 'base.rest.service'
    _name = "ce.landing.services"
    _collection = "ce.services"
    _usage = "landing"
    _description = """
        CE WP landing page requests
    """

    @restapi.method(
        [(["/<int:odoo_landing_page_id>"], "GET")],
        output_param=restapi.CerberusValidator("_validator_create"),
        auth="api_key",
    )
    def get(self, _odoo_landing_page_id):
        landing_page = self.env['landing.page'].browse(_odoo_landing_page_id)
        return self._to_dict(landing_page)

    @staticmethod
    def _to_dict(landing_page):
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

    def _validator_create(self):
        return schemas.S_LANDING_PAGE_CREATE
