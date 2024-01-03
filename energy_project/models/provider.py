from odoo import api, fields, models


class Provider(models.Model):
    _name = "energy_project.provider"
    _description = "Energy Service Provider"

    name = fields.Char()
    service_ids = fields.Many2many(
        "energy_project.service", string="Available Services"
    )
