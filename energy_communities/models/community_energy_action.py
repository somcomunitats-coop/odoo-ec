from odoo import fields, models


class CommunityEnergyAction(models.Model):
    _name = "community.energy.action"
    _description = "Community energy action"

    energy_action_id = fields.Many2one(
        "energy.action",
        string="Energy Action",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
    )
    public_status = fields.Selection(
        [("published", "Published"), ("hidden", "Hidden")],
        string="Public status",
        default="published",
        required=True,
    )
