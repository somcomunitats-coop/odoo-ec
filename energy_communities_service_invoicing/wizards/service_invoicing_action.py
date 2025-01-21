from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

from odoo.addons.energy_communities.utils import contract_utils


class ServiceInvoicingActionWizard(models.TransientModel):
    _name = "service.invoicing.action.wizard"
    _description = "Execute actions on service invoicing"

    service_invoicing_id = fields.Many2one(
        "contract.contract", string="Selected contract"
    )
    execution_date = fields.Date(string="Execution date")

    def execute_activate(self):
        with contract_utils(self.env) as component:
            component.set_contract_active(
                contract_id=self.service_invoicing_id,
                activation_date="2025-03-01",
            )
