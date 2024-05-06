from odoo import api, fields, models
from odoo.tools.translate import _


class CmPlace(models.Model):
    _inherit = "cm.place"

    landing_reference = fields.Many2one(
        "landing.page",
        string=_("Landing reference"),
        compute="_compute_landing_reference",
        store=False,
    )

    def _compute_landing_reference(self):
        for rec in self:
            rec.landing_reference = (
                self.env["landing.page"]
                .sudo()
                .search([("map_place_id", "=", self.id)], limit=1)
            )
