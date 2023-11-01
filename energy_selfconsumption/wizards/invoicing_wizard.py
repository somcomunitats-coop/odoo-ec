from odoo import _, fields, models


class InvoicingWizard(models.TransientModel):
    _name = "energy_selfconsumption.invoicing.wizard"

    power = fields.Float(string="Total Energy Generated (kWh)")

    def generate_invoices(self):
        return True
