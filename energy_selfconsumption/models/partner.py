from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _compute_supply_point_count(self):
        for record in self:
            record.supply_point_count = len(record.supply_ids)

    supply_ids = fields.One2many(
        "energy_selfconsumption.supply_point", "owner_id", readonly=True
    )
    supply_point_count = fields.Integer(compute=_compute_supply_point_count)

    def get_supply_points(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Supply Points',
            'view_mode': 'tree,form',
            'res_model': 'energy_selfconsumption.supply_point',
            'domain': [('owner_id', '=', self.id)],
            'context': {'create': True, 'default_owner_id': self.id, 'default_country_id': self.env.ref('base.es').id},
        }
