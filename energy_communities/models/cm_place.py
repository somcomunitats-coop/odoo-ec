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

    def update_external_place_button_translation(self):
        if (
            self.marker_color.id
            == self.env.ref("energy_communities.map_filter_external").id
        ):
            translations = {
                "es_ES": "Ponte en contacto",
                "ca_ES": "Posa-t’hi en contacte",
                "eu_ES": "Jarri harremanetan",
            }
            # print(place.external_link_ids)
            if self.external_link_ids:
                for lang in translations.keys():
                    self.external_link_ids[0].with_context({"lang": lang}).write(
                        {"name": translations[lang]}
                    )
            return True
