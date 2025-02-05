from odoo import _, fields, models

from ..backends import ArkenovaBackend


class Provider(models.Model):
    _name = "energy_project.provider"
    _description = "Energy Service Provider"

    name = fields.Char(
        string=_("Name"),
        help=_("Name of the provider"),
    )
    service_available_ids = fields.One2many(
        "energy_project.service_available", "provider_id"
    )
    user_id = fields.Many2one(
        "res.users",
        required=True,
        string=_("User"),
        help=_("User related with this provider"),
    )

    uri = fields.Char(
        string=_("URI"),
        help=_(
            "If a provider has an API, URI of that API. Ex: https://api.provider.com"
        ),
    )

    token = fields.Char(
        string=_("Token"),
        help=_("If a provadir has an API, token for autentication / authorization"),
    )

    def backend(self):
        if "arkenova" in self.name.lower():
            return ArkenovaBackend(self.uri, self.token)
