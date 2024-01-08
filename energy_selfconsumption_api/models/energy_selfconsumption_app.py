from odoo import _, api, fields, models

from ..routers import router

APP_NAME = "energy_selfconsumption"


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
