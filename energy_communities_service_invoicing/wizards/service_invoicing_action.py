from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

from odoo.addons.energy_communities.utils import contract_utils

from ..config import SERVICE_INVOICING_EXECUTED_ACTION_VALUES
from ..utils import service_invoicing_form_view_for_platform_admins


class ServiceInvoicingActionWizard(models.TransientModel):
    _name = "service.invoicing.action.wizard"
    _description = "Execute actions on service invoicing"

    service_invoicing_id = fields.Many2one(
        "contract.contract", string="Selected contract"
    )
    execution_date = fields.Date(string="Execution date")
    executed_action = fields.Selection(
        selection=SERVICE_INVOICING_EXECUTED_ACTION_VALUES
    )
    pricelist_id = fields.Many2one("product.pricelist", string="Select pricelist")
    pack_id = fields.Many2one("product.product", string="Pack")
    discount = fields.Float(string="Discount (%)", digits="Discount")
    payment_mode_id = fields.Many2one("account.payment.mode", string="Payment mode")
    pack_type = fields.Selection(related="service_invoicing_id.pack_type")

    def execute_activate(self):
        with contract_utils(self.env, self.service_invoicing_id) as component:
            component.activate(self.execution_date)

    def execute_close(self):
        with contract_utils(self.env, self.service_invoicing_id) as component:
            component.close(self.execution_date)

    def execute_modify(self):
        self._validate_execute_modify()
        executed_modification_action = self._build_executed_modification_action()
        with contract_utils(self.env, self.service_invoicing_id) as component:
            service_invoicing_id = component.modify(
                self.execution_date,
                executed_modification_action,
                self.pricelist_id,
                self.pack_id,
                self.discount,
                self.payment_mode_id,
            )
        return service_invoicing_form_view_for_platform_admins(
            self.env, service_invoicing_id
        )

    def execute_reopen(self):
        with contract_utils(self.env, self.service_invoicing_id) as component:
            service_invoicing_id = component.reopen(
                self.execution_date,
                self.pricelist_id,
                self.pack_id,
                self.discount,
                self.payment_mode_id,
            )
        return service_invoicing_form_view_for_platform_admins(
            self.env, service_invoicing_id
        )

    def _validate_execute_modify(self):
        if (
            not self.pricelist_id
            and not self.pack_id
            and not self.payment_mode_id
            and self.discount == self.service_invoicing_id.discount
        ):
            raise ValidationError(_("Select at least one value to modify"))

    def _build_executed_modification_action(self):
        executed_modification_action = ""
        if self.pricelist_id:
            executed_modification_action += "modify_pricelist"
        if self.pack_id:
            if bool(executed_modification_action):
                executed_modification_action += ","
            executed_modification_action += "modify_pack"
        if self.payment_mode_id:
            if bool(executed_modification_action):
                executed_modification_action += ","
            executed_modification_action += "modify_payment_mode"
        if self.discount != self.service_invoicing_id.discount:
            if bool(executed_modification_action):
                executed_modification_action += ","
            executed_modification_action += "modify_discount"
        return executed_modification_action
