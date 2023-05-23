from odoo import fields, models, api


class SupplyPointAssignation(models.Model):
    _name = 'energy_selfconsumption.supply_point_assignation'
    _description = 'Supply Point Assignation'

    distribution_table_id = fields.Many2one('energy_selfconsumption.distribution_table', required=True)
    supply_point_id = fields.Many2one('energy_selfconsumption.supply_point', required=True)
    coefficient = fields.Float(string='Distribution coefficient')
    owner_id = fields.Many2one("res.partner", related='supply_point_id.owner_id')

