from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

STATE_VALUES = [
    ("draft", _("Draft")),
    ("active", _("Active")),
]

TYPE_VALUES = [
    ("fixed", _("Fixed")),
    ("horary", _("Horary")),
]


class DistributionTable(models.Model):
    _name = 'energy_selfconsumption.distribution_table'
    _description = 'Distribution Table'

    @api.depends('supply_point_assignation_ids.coefficient')
    def _compute_coefficient_is_valid(self):
        for record in self:
            record.coefficient_is_valid = not fields.Float.compare(
                sum(record.supply_point_assignation_ids.mapped('coefficient')), 1.00000,
                precision_rounding=0.00001)

    name = fields.Char()
    selfconsumption_project_id = fields.Many2one('energy_selfconsumption.selfconsumption', required=True)
    type = fields.Selection(TYPE_VALUES, default="fixed", required=True, string="Modality")
    state = fields.Selection(STATE_VALUES, default="draft", required=True)
    supply_point_assignation_ids = fields.One2many('energy_selfconsumption.supply_point_assignation',
                                                   'distribution_table_id')
    coefficient_is_valid = fields.Boolean(compute=_compute_coefficient_is_valid, readonly=True, store=False)
    active = fields.Boolean(default=True)

    @api.onchange('selfconsumption_project_id')
    def _onchange_selfconsumption_project_id(self):
        self.supply_point_assignation_ids = False

    def button_activate(self):
        for record in self:
            if not record.coefficient_is_valid:
                raise ValidationError(_("Coefficient distribution must sum to 1."))
            if not record.selfconsumption_project_id.state == 'activation':
                raise ValidationError(_("Self-consumption project is not in activation"))
            record.write({"state": "active"})
