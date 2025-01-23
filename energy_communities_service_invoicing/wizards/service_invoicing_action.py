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
    executed_action = fields.Selection(
        [
            ("activate", _("Activate")),
            ("close", _("Close")),
            ("modify_pack", _("Modify pack")),
            ("modify_pricelist", _("Modify pricelist")),
        ]
    )

    def execute_activate(self):
        with contract_utils(self.env, self.service_invoicing_id) as component:
            component.set_contract_active(self.execution_date)

    def execute_close(self):
        with contract_utils(self.env, self.service_invoicing_id) as component:
            component.set_contract_closed(self.execution_date)
