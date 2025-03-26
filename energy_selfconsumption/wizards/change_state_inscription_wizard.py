import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)

STATE_VALUES = [
    ("active", _("Active")),
    ("inactive", _("Inactive")),
    ("change", _("Change")),
]


class ChangeStateInscriptionWizard(models.TransientModel):
    _name = "energy_selfconsumption.change_state_inscription.wizard"
    _description = "Service to generate distribution table"

    change_state_inscription_lines_wizard_ids = fields.One2many(
        "energy_selfconsumption.change_state_inscription_lines.wizard",
        "change_state_inscription_wizard_id",
        string="Change state inscription lines wizards",
    )

    @api.model
    def default_get(self, default_fields):
        # OVERRIDE
        default_fields = super().default_get(default_fields)

        if len(self.env.context.get("active_ids", [])) == 0:
            raise ValidationError(_("You have to select at least one entry."))

        lines = []
        for inscription_id in self.env.context["active_ids"]:
            inscription = self.env[
                "energy_selfconsumption.inscription_selfconsumption"
            ].browse(inscription_id)
            lines.append(
                (
                    0,
                    0,
                    {
                        "change_state_inscription_wizard_id": self.id,
                        "inscription_id": inscription.id,
                        "state": inscription.state,
                        "participation_real_quantity": inscription.participation_real_quantity
                        if inscription.state == "active"
                        else inscription.participation_assigned_quantity,
                    },
                )
            )

        default_fields["change_state_inscription_lines_wizard_ids"] = lines

        return default_fields

    def change_state_inscription(self):
        for (
            change_state_inscription_lines_wizard
        ) in self.change_state_inscription_lines_wizard_ids:
            inscription = change_state_inscription_lines_wizard.inscription_id
            vals = {}
            if inscription.state != change_state_inscription_lines_wizard.state:
                vals["state"] = change_state_inscription_lines_wizard.state
            if (
                round(inscription.participation_assigned_quantity, 2)
                != round(
                    change_state_inscription_lines_wizard.participation_real_quantity, 2
                )
                and inscription.state != "active"
            ) or (
                round(inscription.participation_real_quantity, 2)
                != round(
                    change_state_inscription_lines_wizard.participation_real_quantity, 2
                )
                and inscription.state == "active"
            ):
                vals[
                    "participation_assigned_quantity"
                ] = change_state_inscription_lines_wizard.participation_real_quantity
            if vals != {}:
                inscription.update(vals)
        return True


class ChangeStateInscriptionLinesWizard(models.TransientModel):
    _name = "energy_selfconsumption.change_state_inscription_lines.wizard"
    _description = "Service to change state of inscription lines"

    change_state_inscription_wizard_id = fields.Many2one(
        "energy_selfconsumption.change_state_inscription.wizard",
        string="Change state inscription wizard",
        required=True,
    )

    inscription_id = fields.Many2one(
        "energy_selfconsumption.inscription_selfconsumption",
        string="Inscription",
        required=True,
    )

    state = fields.Selection(STATE_VALUES, required=True, string="Status")

    participation_real_quantity = fields.Float(
        string="Participation real quantity", required=True
    )

    @api.onchange("participation_real_quantity")
    def _onchange_participation_real_quantity(self):
        if (
            round(self.participation_real_quantity, 2)
            != round(self.inscription_id.participation_real_quantity, 2)
            and self.state == "active"
        ):
            self.state = "change"
        if (
            round(self.participation_real_quantity, 2)
            == round(self.inscription_id.participation_real_quantity, 2)
            and self.state == "change"
        ):
            self.state = "active"
