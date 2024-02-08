from odoo import _, api, fields, models


class ServiceAvailable(models.Model):
    _name = "energy_project.service_available"
    _description = "Service Available"

    _sql_constraints = {
        (
            "unique_service_id_provider_id",
            "unique (service_id, provider_id)",
            _("This service is already assigned to this provider."),
        )
    }

    service_id = fields.Many2one("energy_project.service")
    provider_id = fields.Many2one("energy_project.provider")
