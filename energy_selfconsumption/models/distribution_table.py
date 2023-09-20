from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


STATE_VALUES = [
    ("draft", _("Draft")),
    ("validated", _("Validated")),
    ("process", _("In process")),
    ("active", _("Active")),
]

TYPE_VALUES = [("fixed", _("Fixed"))]


class DistributionTable(models.Model):
    _name = "energy_selfconsumption.distribution_table"
    _description = "Distribution Table"

    @api.depends("supply_point_assignation_ids.coefficient")
    def _compute_coefficient_is_valid(self):
        for record in self:
            record.coefficient_is_valid = not fields.Float.compare(
                sum(record.supply_point_assignation_ids.mapped("coefficient")),
                1.00000,
                precision_rounding=0.00001,
            )

    name = fields.Char(readonly=True)
    selfconsumption_project_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption", required=True
    )
    selfconsumption_project_state = fields.Selection(
        related="selfconsumption_project_id.state"
    )
    type = fields.Selection(
        TYPE_VALUES, default="fixed", required=True, string="Modality"
    )
    state = fields.Selection(STATE_VALUES, default="draft", required=True)
    supply_point_assignation_ids = fields.One2many(
        "energy_selfconsumption.supply_point_assignation", "distribution_table_id"
    )
    coefficient_is_valid = fields.Boolean(
        compute=_compute_coefficient_is_valid, readonly=True, store=False
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, readonly=True
    )

    @api.model
    def create(self, vals):
        vals['name'] = self.env.ref('energy_selfconsumption.distribution_table_sequence', False).next_by_id()
        return super(DistributionTable, self).create(vals)

    @api.constrains('supply_point_assignation_ids')
    def _supply_point_constrain(self):
        for record in self:
            if record.state in ('validated', 'process', 'active'):
                raise ValidationError(_("The supply point can't be removed because the distribution table state is {table_state}").format(table_state=record.state))
     
    @api.onchange('selfconsumption_project_id')
    def _onchange_selfconsumption_project_id(self):
        self.supply_point_assignation_ids = False

    def button_validate(self):
        for record in self:
            if not record.coefficient_is_valid:
                raise ValidationError(_("Coefficient distribution must sum to 1."))
            if record.selfconsumption_project_id.distribution_table_ids.filtered_domain(
                [("state", "=", "validated")]
            ):
                raise ValidationError(
                    _("Self-consumption project already has a validated table")
                )
            if record.selfconsumption_project_id.distribution_table_ids.filtered_domain(
                [("state", "=", "process")]
            ):
                raise ValidationError(
                    _("Self-consumption project already has a table in process")
                )
            record.write({"state": "validated"})

    def button_draft(self):
        for record in self:
            record.write({"state": "draft"})

    def action_distribution_table_import_wizard(self):
        self.ensure_one()
        return {
            "name": _("Import Distribution Table"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "energy_selfconsumption.distribution_table_import.wizard",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
        }
