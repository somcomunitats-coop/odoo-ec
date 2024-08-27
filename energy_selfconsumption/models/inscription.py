from odoo import fields, models

class Inscription(models.Model):
    _name = "energy_selfconsumption.inscription_selfconsumption"
    _inherits = {
        "energy_project.inscription": "inscription_id",
    }
    _description = "Inscriptions for a self-consumption"

    inscription_id = fields.Many2one(
        "energy_project.inscription", required=True, ondelete="cascade"
    )
    annual_electricity_use = fields.Float(string="Annual electricity use")
    participation = fields.Many2one(
        comodel_name="energy_project.participation",
        string="Participation"
    )
    accept = fields.Boolean(String="I accept and authorize being able to issue payments"
                                   " to this bank account as part of participation in "
                                   "this shared self-consumption project of my energy "
                                   "community")
    member = fields.Boolean(String="is a member?")
