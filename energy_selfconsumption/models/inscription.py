from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

STATE_VALUES = [
    ("active", _("Active")),
    ("inactive", _("Inactive")),
    ("change", _("Change")),
    ("cancelled", _("Cancelled")),
]


class Inscription(models.Model):
    _name = "energy_selfconsumption.inscription_selfconsumption"
    _inherits = {
        "energy_project.inscription": "inscription_id",
    }
    _description = "Inscriptions for a self-consumption"

    inscription_id = fields.Many2one(
        "energy_project.inscription", required=True, ondelete="cascade"
    )
    selfconsumption_project_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption",
        required=True,
        ondelete="restrict",
        string="Self-consumption Energy Project",
        check_company=True,
    )
    annual_electricity_use = fields.Float(string="Annual electricity use")
    participation_id = fields.Many2one(
        comodel_name="energy_selfconsumptions.participation", string="Participation"
    )
    participation_quantity = fields.Float(
        string="Requested participation", related="participation_id.quantity"
    )
    participation_assigned_quantity = fields.Float(
        string="Agreed participation",
        default=lambda self: self.participation_id.quantity,
    )
    participation_real_quantity = fields.Float(
        string="Actual participation",
        default=lambda self: self.participation_id.quantity,
    )
    state = fields.Selection(
        string="Status",
        selection=STATE_VALUES,
        default="inactive",
    )
    accept = fields.Boolean(
        string="I accept and authorize being able to issue payments"
        " to this bank account as part of participation in "
        "this shared self-consumption project of my energy "
        "community"
    )
    member = fields.Boolean(string="Member/Non-Member")
    supply_point_id = fields.Many2one(
        "energy_selfconsumption.supply_point", required=True
    )
    owner_id = fields.Many2one(
        related="supply_point_id.owner_id",
        string="Owner",
    )
    code = fields.Char(string="CUPS", related="supply_point_id.code")
    used_in_selfconsumption = fields.Selection(
        string="Used in selfconsumption",
        related="supply_point_id.used_in_selfconsumption",
    )
    vulnerability_situation = fields.Selection(
        string="Vulnerability situation",
        related="supply_point_id.owner_id.vulnerability_situation",
    )

    @api.onchange("participation_assigned_quantity")
    def _onchange_participation_assigned_quantity(self):
        if (
            self.participation_assigned_quantity != self.participation_quantity
            and self.state == "active"
        ):
            self.state = "change"

    @api.constrains("project_id", "partner_id", "supply_point_id")
    def _constraint_unique(self):
        for record in self:
            exist = self.search(
                [
                    ("id", "!=", record.id),
                    ("project_id", "=", record.project_id.id),
                    ("partner_id", "=", record.partner_id.id),
                    ("supply_point_id", "=", record.supply_point_id.id),
                ]
            )
            if exist:
                raise ValidationError(
                    _("Partner is already signed up in this project with that cups.")
                )

    def create_participant_table(self):
        ctx = self.env.context.copy()
        action = self.env.ref(
            "energy_selfconsumption.create_distribution_table_wizard_action"
        ).read()[0]
        action["context"] = ctx
        return action

    def change_state_inscription(self):
        ctx = self.env.context.copy()
        action = self.env.ref(
            "energy_selfconsumption.change_state_inscription_wizard_action"
        ).read()[0]
        action["context"] = ctx
        return action

    def unlink(self):
        for inscription in self:
            inscription.inscription_id.unlink()
        return super().unlink()
