from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Inscription(models.Model):
    _name = "energy_selfconsumption.inscription_selfconsumption"
    _inherits = {
        "energy_project.inscription": "inscription_id",
    }
    _description = "Inscriptions for a self-consumption"

    _sql_constraints = {
        (
            "unique_project_id_partner_id_code",
            "unique (project_id, partner_id, code)",
            _("Partner is already signed up in this project with that cups."),
        )
    }

    _USED_IN_SELFCONSUMPTION_VALUES = [
        ("yes", _("Yes")),
        ("no", _("No")),
    ]

    _VULNERABILITY_SITUATION_VALUES = [
        ("yes", _("Yes")),
        ("no", _("No")),
    ]

    inscription_id = fields.Many2one(
        "energy_project.inscription", required=True, ondelete="cascade"
    )
    annual_electricity_use = fields.Float(string="Annual electricity use")
    participation = fields.Many2one(
        comodel_name="energy_project.participation", string="Participation"
    )
    participation_quantity = fields.Float(
        string="Participation", related="participation.quantity"
    )
    accept = fields.Boolean(
        String="I accept and authorize being able to issue payments"
        " to this bank account as part of participation in "
        "this shared self-consumption project of my energy "
        "community"
    )
    member = fields.Boolean(String="Member/Non-Member")
    supply_point_id = fields.Many2one(
        "energy_selfconsumption.supply_point", required=True
    )
    code = fields.Char(string="CUPS", related="supply_point_id.code")
    used_in_selfconsumption = fields.Selection(
        _USED_IN_SELFCONSUMPTION_VALUES,
        string="Used in selfconsumption",
        related="supply_point_id.used_in_selfconsumption",
    )
    vulnerability_situation = fields.Selection(
        _VULNERABILITY_SITUATION_VALUES,
        string="Vulnerability situation",
        related="partner_id.vulnerability_situation",
    )

    def create_participant_table(self):
        ctx = self.env.context.copy()
        action = self.env.ref(
            "energy_selfconsumption.create_distribution_table_wizard_action"
        ).read()[0]
        action["context"] = ctx
        return action

    def unlink(self):
        for inscription in self:
            inscription.inscription_id.unlink()
        return super().unlink()
