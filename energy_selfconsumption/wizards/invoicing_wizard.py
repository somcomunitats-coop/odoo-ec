from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class InvoicingWizard(models.TransientModel):
    _name = "energy_selfconsumption.invoicing.wizard"

    power = fields.Float(string="Total Energy Generated (kWh)")
    contract_ids = fields.Many2many("contract.contract", readonly=True)

    @api.constrains("contract_ids")
    def constraint_contract_ids(self):
        for record in self:
            contract_list = record.contract_ids
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
        return self.with_context(
            {"energy_delivered": self.power}
        ).contract_ids._recurring_create_invoice()
