from odoo import _, api, fields, models


class ServiceAssignation(models.Model):
    _name = "energy_project.service_assignation"
    _description = "Energy Services Assignation"

    _sql_constraints = {
        (
            "unique_service_id_provider_id_project_id",
            "unique (service_id, provider_id, project_id)",
            _("There's already a service with this provider assigned to this project."),
        )
    }

    service_id = fields.Many2one(
        "energy_project.service", string="Service", required=True
    )
    provider_id = fields.Many2one(
        "energy_project.provider", string="Provider", required=True
    )
    project_id = fields.Many2one("energy_project.project", required=True)
