from odoo import _, api, fields, models

from ..client_map.config import MapClientConfig


class LandingCooperatorButton(models.Model):
    _name = "landing.cooperator.button"
    _description = "Landing page"

    name = fields.Char(string="Name", translate=True)
    url = fields.Char(string="Url")
    mode = fields.Selection(
        [
            ("custom", _("Custom")),
            ("contact", _("Contact")),
            ("become_cooperator", _("Become Cooperator")),
            ("become_company_cooperator", _("Become company cooperator")),
        ],
        string="Mode",
        default="custom",
    )
    visibility = fields.Selection(
        [("hidden", _("Hidden")), ("visible", _("Visible"))],
        string="Visibility",
        default="visible",
    )
    landing_page_id = fields.Many2one("landing.page", string="Landing Page")
