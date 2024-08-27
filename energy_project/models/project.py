from odoo import _, fields, models

from ..services.monitoring_service import MonitoringService

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
    company_name = fields.Char(
        string="Name of the company", related="company_id.name", store=False
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

    def monitoring_service(self):
        self.ensure_one()
        service_name = self.env.ref("energy_project.monitoring_service").name
        monitoring_contract = self.service_contract_ids.filtered(
            lambda service_contract: service_contract.active == True
            and service_contract.service_id.name == service_name
        )
        if monitoring_contract:
            return MonitoringService(
                monitoring_contract.provider_id.backend(), monitoring_contract
            )
