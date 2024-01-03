from odoo import api, fields, models


class ServiceAssignation(models.Model):
    _name = "energy_project.service_assignation"
    _description = "Energy Services Assignation"

    service_id = fields.Many2one(
        "energy_project.service", string="Service", required=True
    )
    provider_id = fields.Many2one(
        "energy_project.provider", string="Provider", required=True
    )
    project_id = fields.Many2one("energy_project.project")
