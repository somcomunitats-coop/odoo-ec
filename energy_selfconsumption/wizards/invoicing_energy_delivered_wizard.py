from odoo import _, fields, models


class InvoicingEnergyDeliveredWizard(models.TransientModel):
    _name = "energy_selfconsumption.invoicing_energy_delivered.wizard"

    power = fields.Float(string="Total Energy Generated (kWh)")

    def generate_invoices(self):
        return True
