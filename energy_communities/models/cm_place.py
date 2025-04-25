from odoo import api, fields, models
from odoo.tools.translate import _


class CmPlace(models.Model):
    _name = "cm.place"
    _inherit = ["cm.place", "user.currentcompany.mixin"]

    landing_id = fields.Many2one(
        "landing.page",
        string=_("Landing reference"),
    )
    key_group_activated = fields.Boolean(string="Key group activated")
