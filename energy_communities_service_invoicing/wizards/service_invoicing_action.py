from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

from odoo.addons.energy_communities.utils import contract_utils

from ..utils import (
    _SERVICE_INVOICING_EXECUTED_ACTION_VALUES,
    service_invoicing_view,
)


class ServiceInvoicingActionWizard(models.TransientModel):
    _name = "service.invoicing.action.wizard"
    _description = "Execute actions on service invoicing"

    service_invoicing_id = fields.Many2one(
        "contract.contract", string="Selected contract"
    )
    execution_date = fields.Date(string="Execution date")
    executed_action = fields.Selection(
        selection=_SERVICE_INVOICING_EXECUTED_ACTION_VALUES
    )
    pricelist_id = fields.Many2one("product.pricelist", string="Select pricelist")
    service_pack_id = fields.Many2one("product.product", string="Service pack")

    def execute_activate(self):
        with contract_utils(self.env, self.service_invoicing_id) as component:
            component.set_contract_status_active(self.execution_date)

    def execute_close(self):
        with contract_utils(self.env, self.service_invoicing_id) as component:
            component.set_contract_status_closed(self.execution_date)

    def execute_modify(self):
        self._validate_execute_modify()
        executed_modification_action = self._build_executed_modification_action()
        with contract_utils(self.env, self.service_invoicing_id) as component:
            service_invoicing_id = component.modify(
                self.execution_date,
                executed_modification_action,
                self.pricelist_id,
                self.service_pack_id,
            )
        return service_invoicing_view(self.env, service_invoicing_id)

    def execute_reopen(self):
        with contract_utils(self.env, self.service_invoicing_id) as component:
            service_invoicing_id = component.reopen(
                self.execution_date,
                self.pricelist_id,
                self.service_pack_id,
            )
        return service_invoicing_view(self.env, service_invoicing_id)

    def _validate_execute_modify(self):
        if not self.pricelist_id and not self.service_pack_id:
            raise ValidationError(_("Select at least one value to modify"))

    def _build_executed_modification_action(self):
        executed_modification_action = ""
        if self.pricelist_id:
            executed_modification_action += "modify_pricelist"
        if self.service_pack_id:
            if bool(executed_modification_action):
                executed_modification_action += ","
            executed_modification_action += "modify_service_pack"
        return executed_modification_action
