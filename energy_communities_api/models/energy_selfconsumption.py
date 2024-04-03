from fastapi import Depends

from odoo import _, api, fields, models

from odoo.addons.fastapi.dependencies import authenticated_partner_impl

from ..dependencies import api_key_authentication
from ..routers.energy_selfconsumption import router

APP_NAME = "energy_selfconsumption_api"


class EnergySelfConsumptionAPI(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[(APP_NAME, _("Energy selfconsumption api app"))],
        ondelete={APP_NAME: "cascade"},
    )

    @api.model
    def _get_fastapi_routers(self):
        if self.app == APP_NAME:
            return [router]
        return super()._get_fastapi_routers()

    def _get_app(self):
        app = super()._get_app()
        if self.app == APP_NAME:
            app.dependency_overrides[
                authenticated_partner_impl
            ] = api_key_authentication
        return app
