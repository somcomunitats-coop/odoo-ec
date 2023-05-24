from odoo import fields, models, api


class SupplyPointAssignation(models.Model):
    _name = 'energy_selfconsumption.supply_point_assignation'
    _description = 'Supply Point Assignation'

    @api.depends('distribution_table_id')
    def _compute_supply_point_filtered_ids(self):
        for record in self:
            record.supply_point_filtered_ids = record.distribution_table_id.selfconsumption_project_id.inscription_ids.mapped('partner_id.supply_ids')


    distribution_table_id = fields.Many2one('energy_selfconsumption.distribution_table', required=True)
    supply_point_id = fields.Many2one('energy_selfconsumption.supply_point', required=True)
    coefficient = fields.Float(string='Distribution coefficient')
    owner_id = fields.Many2one("res.partner", related='supply_point_id.owner_id')
    table_coefficient_is_valid = fields.Boolean(related='distribution_table_id.coefficient_is_valid')

    supply_point_filtered_ids = fields.One2many('energy_selfconsumption.supply_point',
                                                compute=_compute_supply_point_filtered_ids, readonly=True)
