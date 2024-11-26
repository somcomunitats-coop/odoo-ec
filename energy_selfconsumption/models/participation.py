from odoo import fields, models


class Participation(models.Model):
    _name = "energy_project.participation"
    _description = "Participation inscription"

    name = fields.Char(string="Description")
    quantity = fields.Float(string="Quantity")
    project_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption", required=True, ondelete="cascade"
    )
