from odoo import fields, models, api


class SelfconsumptionImportWizard(models.TransientModel):
    _name = 'energy_selfconsumption.selfconsumption_import.wizard'

    name = fields.Char()
