from odoo import api, fields, models


class Service(models.Model):
    _name = "energy_project.service"
    _description = "Energy Services"

    name = fields.Char()
    service_available_ids = fields.One2many(
        "energy_project.service_available", "service_id"
    )
