from odoo import _, fields, models
from odoo.exceptions import ValidationError


class Selfconsumption(models.Model):
    _name = "energy_selfconsumption.selfconsumption"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _inherits = {
        "energy_project.project": "project_id",
    }
    _description = "Self-consumption Energy Project"

    def _compute_distribution_table_count(self):
        for record in self:
            record.distribution_table_count = len(record.distribution_table_ids)

    def _compute_inscription_count(self):
        for record in self:
            record.inscription_count = len(record.inscription_ids)

    project_id = fields.Many2one(
        "energy_project.project", required=True, ondelete="cascade"
    )
    code = fields.Char(string="CAU")
    cil = fields.Char(string="CIL", help="Production facility code for liquidation purposes")
    owner_id = fields.Many2one("res.partner", string="Owner", required=True, default=lambda self: self.env.company.partner_id)
    power = fields.Float(string="Generation Power (kW)")
    distribution_table_ids = fields.One2many('energy_selfconsumption.distribution_table', 'selfconsumption_project_id',
                                             readonly=True)
    distribution_table_count = fields.Integer(compute=_compute_distribution_table_count) 
    inscription_ids = fields.One2many('energy_project.inscription', 'project_id', readonly=True)
    inscription_count = fields.Integer(compute=_compute_inscription_count)

    def get_distribution_tables(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Distribution Tables',
            'view_mode': 'tree,form',
            'res_model': 'energy_selfconsumption.distribution_table',
            'domain': [('selfconsumption_project_id', '=', self.id)],
            'context': {'create': True, 'default_selfconsumption_project_id': self.id},
        }
    
    def get_inscriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inscriptions',
            'view_mode': 'tree,form',
            'res_model': 'energy_project.inscription',
            'domain': [('project_id', '=', self.id)],
            'context': {'create': True, 'default_project_id': self.id},
        }

    def set_activation(self):
        for record in self:
            record.write({"state": "activation"})

    def activate(self):
        for record in self:
            if not record.code:
                raise ValidationError(_("Project must have a valid Code."))
            if not record.cil:
                raise ValidationError(_("Project must have a valid CIL."))
            if not record.power or record.power <= 0:
                raise ValidationError(_("Project must have a valid Generation Power."))
            if not record.distribution_table_ids.filtered_domain([('state', '=', 'validated')]):
                raise ValidationError(_("Must have a valid Distribution Table."))
            record.write({"state": "active"})
