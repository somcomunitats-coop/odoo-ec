import logging

from odoo.addons.component.core import Component

from . import schemas

_logger = logging.getLogger(__name__)


class OpendataLandingPageService(Component):
    _inherit = ["base.rest.service"]
    _name = "opendata_landingpage.api.service"
    _collection = "opendata.api.services"
    _usage = "landing"
    _description = """
        Set of endpoints that return opendata about energy communites public website page
    """

    def get(self, _id):
        related_company = self.env["res.company"].browse(_id)
        return self._to_dict(related_company.landing_page_id)

    @staticmethod
    def _to_dict(landing_page):
        return landing_page.to_dict()

    def _validator_get(self):
        return {}

    def _validator_return_get(self):
        return schemas.S_LANDING_PAGE_GET_RETURN
