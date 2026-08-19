from odoo import _, fields, models
from odoo.exceptions import ValidationError


class SetNewDistributionTableWizard(models.TransientModel):
    """
    Wizard to set a new distribution table with a chosen execution date.
    """

    _name = "energy_selfconsumption.set_new_distribution_table.wizard"
    _description = "Set New Distribution Table Wizard"

    selfconsumption_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption",
        string="Self-consumption Project",
        required=True,
        readonly=True,
        help="Self-consumption project where the distribution table will be set",
    )
    execution_date = fields.Date(
        string="Distribution table change date",
        required=True,
        default=fields.Date.context_today,
        help="Date when the new distribution table will take effect",
    )

    def action_confirm(self):
        """Confirm and set the new distribution table using the selected date."""
        self.ensure_one()
        if not self.selfconsumption_id:
            raise ValidationError(_("No self-consumption project selected"))
        if not self.execution_date:
            raise ValidationError(_("Distribution table change date is required"))

        self.selfconsumption_id.set_new_distribution_table(
            execution_date=self.execution_date
        )
        return {"type": "ir.actions.act_window_close"}
