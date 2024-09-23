from odoo import _, api, fields, models


class EnergyAction(models.Model):
    _name = "energy.action"

    name = fields.Char(string="Name")
