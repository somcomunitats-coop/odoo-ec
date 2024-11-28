from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
    participation = fields.Many2one(
        comodel_name="energy_project.participation", string="Participation"
    )
    participation_quantity = fields.Float(
        string="Participation", related="participation.quantity"
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
    code = fields.Char(string="CUPS", related="supply_point_id.code")
    used_in_selfconsumption = fields.Selection(
        string="Used in selfconsumption",
        related="supply_point_id.used_in_selfconsumption",
    )
    vulnerability_situation = fields.Selection(
        string="Vulnerability situation",
        related="partner_id.vulnerability_situation",
    )

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

    def unlink(self):
        for inscription in self:
            inscription.inscription_id.unlink()
        return super().unlink()
