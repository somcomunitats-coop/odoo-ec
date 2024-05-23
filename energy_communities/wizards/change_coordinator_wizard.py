from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class ChangeCoordinatorWizard(models.TransientModel):
    _name = "change.coordinator.wizard"
    _description = "Change the coordinator of an existing energy community"

    coordinator_destination = fields.Many2one(
        "res.company", string="Destination Coordinator"
    )

    def execute_change(self):
        print("DONE!")
