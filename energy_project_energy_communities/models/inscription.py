from odoo import fields, models


class Inscription(models.Model):
    _inherit = "energy_project.inscription"

    partner_id = fields.Many2one(domain=[("member", "=", True)])
