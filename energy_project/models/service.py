from odoo import api, fields, models


class Service(models.Model):
    _name = "energy_project.service"
    _description = "Energy Services"

    name = fields.Char()
    # Inverse of service_ids in energy_project.provider
    provider_ids = fields.Many2many(
        "energy_project.provider",
        string="Available Providers",
        relation="provider_service_rel",
        column1="service_id",
        column2="provider_id",
    )
