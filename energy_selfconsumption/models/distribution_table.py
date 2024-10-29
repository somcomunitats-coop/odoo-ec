import pandas as pd

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

STATE_VALUES = [
    ("draft", _("Draft")),
    ("validated", _("Validated")),
    ("process", _("In process")),
    ("active", _("Active")),
]

TYPE_VALUES = [("fixed", _("Fixed")), ("hourly", _("Variable hourly"))]


class DistributionTable(models.Model):
    _name = "energy_selfconsumption.distribution_table"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Distribution Table"

    @api.depends("supply_point_assignation_ids.coefficient")
    def _compute_coefficient_is_valid(self):
        for record in self:
            if record.type == "fixed":
                coefficients = record.supply_point_assignation_ids.mapped("coefficient")
                sum_coefficients = sum(coefficients)
                record.coefficient_is_valid = not fields.Float.compare(
                    sum_coefficients,
                    1.000000,
                    precision_rounding=0.000001,
                )
            else:
                record.coefficient_is_valid = True

    name = fields.Char(
        readonly=True,
        default=lambda self: self.env.ref(
            "energy_selfconsumption.distribution_table_sequence", False
        ).next_by_id(),
    )
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

    hourly_coefficients_imported_file = fields.Binary(string="Import File (*.csv)")
    hourly_coefficients_imported_filename = fields.Char(string="File Name")

    hourly_coefficients_imported_delimiter = fields.Char(
        default=",",
        required=True,
        string="File Delimiter",
        help="Delimiter in import CSV file.",
    )
    hourly_coefficients_imported_quotechar = fields.Char(
        default='"',
        required=True,
        string="File Quotechar",
        help="Quotechar in import CSV file.",
    )
    hourly_coefficients_imported_encoding = fields.Char(
        default="utf-8",
        required=True,
        string="File Encoding",
        help="Encoding format in import CSV file.",
    )

    @api.constrains("supply_point_assignation_ids")
    def _supply_point_constrain(self):
        for record in self:
            if record.state in ("validated", "process", "active"):
                raise ValidationError(
                    _(
                        "The supply point can't be removed because the distribution table state is {table_state}"
                    ).format(table_state=record.state)
                )

    def write(self, vals):
        if "type" in vals and self.supply_point_assignation_ids:
            raise ValidationError(
                _(
                    """To change the type you must first delete the associated distribution points.
                    \n\r Hint: you can delete all the associated distribution points at once using an action."""
                )
            )
        result = super().write(vals)
        return result

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

    def action_clean_supply_point_assignation_wizard(self):
        return {
            "name": _("Clean supply point assignation"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "clean.supply.point.assignation.wizard",
            "target": "new",
            "context": {"active_ids": self.env.context.get("active_ids", [])},
        }
