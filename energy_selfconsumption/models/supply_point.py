from odoo import fields, models


class SupplyPoint(models.Model):
    _name = "energy_selfconsumption.supply_point"
    _description = "Energy Supply Point"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True)
    code = fields.Char(string="CUPS", required=True)
    owner_id = fields.Many2one("res.partner", string="Owner", required=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, readonly=True
    )

    # Address fields
    street = fields.Char(required=True)
    street2 = fields.Char(required=True)
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
        "res.country", string="Country", ondelete="restrict", required=True
    )

    supply_point_assignation_ids = fields.One2many('energy_selfconsumption.supply_point_assignation','supply_point_id',
                                                   readonly=True)
