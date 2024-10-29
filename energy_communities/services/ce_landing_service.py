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
        related_company = self.env["res.company"].browse(_id)
        return self._to_dict(related_company.landing_page_id)

    @staticmethod
    def _to_dict(landing_page):
        return landing_page.to_dict()

    def _validator_get(self):
        return {}

    def _validator_return_get(self):
        return schemas.S_LANDING_PAGE_CREATE
