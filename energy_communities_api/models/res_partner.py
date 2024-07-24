from odoo import api, fields, models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "user.currentcompany.mixin"]

    member_number = fields.Char(compute="_compute_member_number")

    @api.depends("cooperative_membership_id")
    def _compute_member_number(self):
        for record in self:
            record.member_number = (
                record.cooperative_membership_id.cooperator_register_number
            )
