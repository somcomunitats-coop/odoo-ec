from odoo import api, fields, models
from odoo.tools.translate import _


class CmFilter(models.Model):
    _inherit = "cm.filter"

    landing_id = fields.Many2one("landing.page", string="Landing page")
