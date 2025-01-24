from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

from odoo.addons.energy_communities.utils import contract_utils

from ..utils import service_invoicing_view


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
            ("modification", _("Modification")),
        ]
    )
    executed_modification_action = fields.Selection(
        [
            ("modify_all", _("Modify prices and service pack")),
            ("modify_pricelist", _("Modify prices")),
            ("modify_service_pack", _("Modify service pack")),
        ],
        string="Modification action",
    )
    pricelist_id = fields.Many2one("product.pricelist", string="Select pricelist")
    service_pack_id = fields.Many2one("product.product", string="Service pack")

    def execute_activate(self):
        with contract_utils(self.env, self.service_invoicing_id) as component:
            component.set_contract_active(self.execution_date)

    def execute_close(self):
        with contract_utils(self.env, self.service_invoicing_id) as component:
            component.set_contract_closed(self.execution_date)

    def execute_modify(self):
        with contract_utils(self.env, self.service_invoicing_id) as component:
            service_invoicing_id = component.modify(
                self.execution_date,
                self.executed_modification_action,
                self.pricelist_id,
                self.service_pack_id,
            )
        return service_invoicing_view(self.env, service_invoicing_id)
