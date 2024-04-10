from odoo import _, fields, models

STATE_VALUES = [
    ("draft", _("Draft")),
    ("inscription", _("In Inscription")),
    ("activation", _("In Activation")),
    ("active", _("Active")),
]


class Project(models.Model):
    _name = "energy_project.project"
    _description = "Energy project"

    name = fields.Char(required=True)
    type = fields.Many2one("energy_project.project_type", required=True, readonly=True)
    state = fields.Selection(STATE_VALUES, default="draft", required=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, readonly=True
    )
    inscription_ids = fields.One2many(
        "energy_project.inscription",
        "project_id",
    )
    active = fields.Boolean(default=True)
    service_contract_ids = fields.One2many(
        "energy_project.service_contract", "project_id", auto_join=True
    )

    # address fields
    street = fields.Char(required=True)
    street2 = fields.Char()
    zip = fields.Char(change_default=True, required=True)
    city = fields.Char(required=True)
    state_id = fields.Many2one(
        "res.country.state",
        string="State",
        ondelete="restrict",
        domain="[('country_id', '=?', country_id)]",
        required=True,
    )
    country_id = fields.Many2one(
        "res.country",
        string="Country",
        ondelete="restrict",
        required=True,
        default=lambda self: self.env.ref("base.es"),
    )
