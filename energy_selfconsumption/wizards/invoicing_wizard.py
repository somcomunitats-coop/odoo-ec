from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class InvoicingWizard(models.TransientModel):
    _name = "energy_selfconsumption.invoicing.wizard"

    power = fields.Float(string="Total Energy Generated (kWh)")
    contract_ids = fields.Many2many("contract.contract", readonly=True)
    next_period_date_start = fields.Date(
        string="Next Period Start",
        compute="_compute_next_period_date_start_and_end",
        readonly=True,
    )
    next_period_date_end = fields.Date(
        string="Next Period End",
        compute="_compute_next_period_date_start_and_end",
        readonly=True,
    )

    @api.depends("contract_ids")
    def _compute_next_period_date_start_and_end(self):
        for record in self:
            if len(record.contract_ids) > 0:
                record.next_period_date_start = record.contract_ids[
                    0
                ].next_period_date_start
                record.next_period_date_end = record.contract_ids[
                    0
                ].next_period_date_end

    @api.constrains("contract_ids")
    def constraint_contract_ids(self):
        for record in self:
            contract_list = record.contract_ids

            all_same_project = all(
                element.project_id == contract_list[0].project_id
                for element in contract_list
            )
            if not all_same_project:
                raise ValidationError(
                    _(
                        """
Some of the contract selected are not of the same self-consumption project.

Please make sure that you are invoicing for only the same self-consumption project {project_name}.
"""
                    ).format(
                        project_name=contract_list[0].project_id.selfconsumption_id.name
                    )
                )

            valid_invoicing_mode = ["energy_delivered"]

            all_invoicing_mode = all(
                element.project_id.selfconsumption_id.invoicing_mode
                in valid_invoicing_mode
                for element in contract_list
            )
            if not all_invoicing_mode:
                raise ValidationError(
                    _(
                        """
Some of the contract selected are not defined as energy delivered self-consumption projects.

Please make sure that you are invoicing the correct self-consumption project.
"""
                    )
                )

            all_equal_period = all(
                element.next_period_date_start
                == contract_list[0].next_period_date_start
                and element.next_period_date_end
                == contract_list[0].next_period_date_end
                for element in contract_list
            )
            if not all_equal_period:
                raise ValidationError(
                    _(
                        """
Select only contracts with the same period of invoicing.
Make sure that all the selected contracts have the same next period start and end.
Next period start: {next_period_date_start}
Next period end: {next_period_date_end}"""
                    ).format(
                        next_period_date_start=contract_list[0].next_period_date_start,
                        next_period_date_end=contract_list[0].next_period_date_end,
                    )
                )

    @api.constrains("power")
    def constraint_power(self):
        for record in self:
            if not record.power or record.power <= 0:
                raise ValidationError(
                    _("You must enter a valid total energy generated (kWh).")
                )

    def generate_invoices(self):
        for contract in self.contract_ids:
            template_name = contract.contract_template_id.contract_line_ids[0].name
            template_name += _("Energy Delivered: {energy_delivered} kWh")
            contract.contract_line_ids.write(
                {
                    "name": template_name.format(
                        energy_delivered=self.power,
                        code=contract.supply_point_assignation_id.supply_point_id.code,
                        owner_id=contract.supply_point_assignation_id.supply_point_id.owner_id.display_name,
                    )
                }
            )
        return self.with_context(
            {"energy_delivered": self.power}
        ).contract_ids._recurring_create_invoice()
