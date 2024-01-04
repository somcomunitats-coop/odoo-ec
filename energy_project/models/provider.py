from odoo import api, fields, models


class Provider(models.Model):
    _name = "energy_project.provider"
    _description = "Energy Service Provider"

    name = fields.Char()
    # Inverse of provider_ids in energy_project.service
    service_ids = fields.Many2many(
        "energy_project.service",
        string="Available Services",
        relation="provider_service_rel",
        column1="provider_id",
        column2="service_id",
    )
