from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Inscription(models.Model):
    _inherit = "energy_project.inscription"

    partner_id = fields.Many2one(domain=[("member", "=", True)])

    @api.constrains("partner_id")
    def _check_member(self):
        for record in self:
            if record.partner_id and not record.partner_id.member:
                raise ValidationError(_("The selected partner is not a member"))
