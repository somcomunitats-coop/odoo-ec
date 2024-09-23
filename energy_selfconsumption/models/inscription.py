from odoo import fields, models, _, api
from stdnum.es import cups
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

    inscription_id = fields.Many2one(
        "energy_project.inscription", required=True, ondelete="cascade"
    )
    annual_electricity_use = fields.Float(string="Annual electricity use")
    participation = fields.Many2one(
        comodel_name="energy_project.participation", string="Participation"
    )
    participation_quantity = fields.Float(string="Participation",
                                          related="participation.quantity")
    accept = fields.Boolean(
        String="I accept and authorize being able to issue payments"
        " to this bank account as part of participation in "
        "this shared self-consumption project of my energy "
        "community"
    )
    member = fields.Boolean(String="Member/Non-Member")
    code = fields.Char(string="CUPS", required=True)

    @api.constrains("code")
    def _check_valid_code(self):
        for record in self:
            if record.code:
                try:
                    cups.validate(record.code)
                except InvalidLength:
                    error_message = _("Invalid CUPS: The length is incorrect.")
                    raise ValidationError(error_message)
                except InvalidComponent:
                    error_message = _("Invalid CUPS: does not start with 'ES'.")
                    raise ValidationError(error_message)
                except InvalidFormat:
                    error_message = _("Invalid CUPS: has an incorrect format.")
                    raise ValidationError(error_message)
                except InvalidChecksum:
                    error_message = _("Invalid CUPS: The checksum is incorrect.")
                    raise ValidationError(error_message)
