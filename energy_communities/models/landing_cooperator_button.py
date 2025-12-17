from odoo import _, api, fields, models

from ..client_map.resources.landing_cmplace import (
    LandingCmPlace as LandingCmPlaceResource,
)
from ..utils import get_successful_popup_message


class LandingCooperatorButton(models.Model):
    _name = "landing.cooperator.button"
    _description = "Landing page"

    name = fields.Char(string="Name", translate=True)
    url = fields.Char(string="Url", translate=True)
    mode = fields.Selection(
        [
            ("custom", _("Custom")),
            ("contact", _("Contact")),
            ("become_cooperator", _("Become Cooperator")),
            ("become_company_cooperator", _("Become company cooperator")),
            ("landing_page", _("Landing page")),
        ],
        string="Mode",
        default="custom",
    )
    visibility = fields.Selection(
        [
            ("hidden", _("Hidden")),
            ("map_landing", _("Map/Landing")),
            ("map", _("Map")),
            ("landing", _("Landing")),
        ],
        string="Visibility",
        default="map_landing",
    )
    landing_page_id = fields.Many2one("landing.page", string="Landing Page")
    sort_order = fields.Integer(string=_("Sort order"))

    _order = "sort_order asc"

    def to_dict(self):
        return {"name": self.name, "url": self.url}
