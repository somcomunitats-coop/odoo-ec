from odoo import fields, models, api, _

STATE_VALUES = [
    ("draft", _("Draft")),
    ("active", _("Active")),
]

class DistributionTable(models.Model):
    _name = 'energy_selfconsumption.distribution_table'
    _description = 'Distribution Table'

    name = fields.Char()
    selfconsumption_project_id = fields.Many2one('energy_selfconsumption.selfconsumption', required=True)
    state = fields.Selection(STATE_VALUES, default="draft", required=True)
    supply_point_assignations_ids = fields.One2many('energy_selfconsumption.supply_point_assignation', 'distribution_table_id')
