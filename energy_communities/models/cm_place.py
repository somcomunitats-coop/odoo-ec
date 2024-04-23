from odoo import api, fields, models
from odoo.tools.translate import _


class CmPlace(models.Model):
    _inherit = "cm.place"

    landing_reference = fields.Char(
        string=_("Landing reference"), compute="_compute_landing_reference", store=False
    )

    def _compute_landing_reference(self):
        for rec in self:
            rec.landing_reference = self.env["landing.page"].search(
                [("map_place_id", "=", self.id)]
            )
