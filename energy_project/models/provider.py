from odoo import api, fields, models


class Provider(models.Model):
    _name = "energy_project.provider"
    _description = "Energy Service Provider"

    name = fields.Char()
    service_available_ids = fields.One2many(
        "energy_project.service_available", "provider_id"
    )
    user_id = fields.Many2one("res.users", required=True)
