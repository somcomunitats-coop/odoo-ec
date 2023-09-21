from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Inscription(models.Model):
    _inherit = "energy_project.inscription"

    partner_id = fields.Many2one()
