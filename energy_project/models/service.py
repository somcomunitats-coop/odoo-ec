from odoo import api, fields, models


class Service(models.Model):
    _name = "energy_project.service"
    _description = "Energy Services"

    name = fields.Char()
