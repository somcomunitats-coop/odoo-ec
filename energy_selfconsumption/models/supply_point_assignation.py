from odoo import fields, models, api

class SupplyPointAssignation(models.Model):
    _name = 'energy_selfconsumption.supply_point_assignation'
    _description = 'Supply Point Assignation'


    @api.depends('distribution_table_id')
    def _compute_supply_point_filtered_ids(self):
        '''
        List of supply point of partners subscribed to the project and not in the list of the distribution table to
        prevent multiple assignations of same supply point.
        Used to filter out in the view.
        :return:
        '''
        for record in self:
            record.supply_point_filtered_ids = \
                record.distribution_table_id.selfconsumption_project_id.inscription_ids.mapped('partner_id.supply_ids') \
                    .filtered_domain([('id', 'not in', record.distribution_table_id.supply_point_assignation_ids.mapped(
                    'supply_point_id.id'))])

    distribution_table_id = fields.Many2one('energy_selfconsumption.distribution_table', required=True)
    supply_point_id = fields.Many2one('energy_selfconsumption.supply_point', required=True)
    coefficient = fields.Float(string='Distribution coefficient', digits=(1, 5))
    owner_id = fields.Many2one("res.partner", related='supply_point_id.owner_id')
    code = fields.Char(related='supply_point_id.code')
    table_coefficient_is_valid = fields.Boolean(related='distribution_table_id.coefficient_is_valid')

    supply_point_filtered_ids = fields.One2many('energy_selfconsumption.supply_point',
                                                compute=_compute_supply_point_filtered_ids, readonly=True)
