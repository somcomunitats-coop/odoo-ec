from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.tools.translate import _

from ..utils import _CONTRACT_STATUS_VALUES


class ContractContract(models.Model):
    _inherit = "contract.contract"

    community_company_id = fields.Many2one(
        "res.company",
        string="Related community",
        domain="[('hierarchy_level','=','community')]",
    )
    predecessor_contract_id = fields.Many2one(
        "contract.contract", string="Predecessor contract"
    )
    successor_contract_id = fields.Many2one(
        "contract.contract", string="Successor contract"
    )
    status = fields.Selection(
        selection=_CONTRACT_STATUS_VALUES,
        required=True,
        string="Status",
        default="in_progress",
    )
    discount = fields.Float(
        string="Discount (%)",
        digits="Discount",
        compute="_compute_discount",
        store=False,
    )
    last_date_invoiced = fields.Date(
        string="Last Date Invoiced", compute="_compute_last_date_invoiced", store=False
    )
    is_pack = fields.Boolean(related="contract_template_id.is_pack")
    service_pack_id = fields.Many2one(
        "product.product",
        string="Service Pack",
        compute="_compute_service_pack_id",
        store=False,
    )
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order (activation)",
    )
    # On energy_communities all contracts have skip_zero_qty marked by default
    skip_zero_qty = fields.Boolean(default=True)

    @api.depends("contract_line_ids")
    def _compute_discount(self):
        for record in self:
            record.discount = 0
            if record.contract_line_ids:
                record.discount = record.contract_line_ids[0].discount

    @api.depends("contract_line_ids")
    def _compute_last_date_invoiced(self):
        for record in self:
            record.last_date_invoiced = None
            if record.contract_line_ids:
                record.last_date_invoiced = record.contract_line_ids[
                    0
                ].last_date_invoiced

    @api.depends("contract_template_id")
    def _compute_service_pack_id(self):
        for record in self:
            record.service_pack_id = False
            if record.contract_template_id:
                rel_product = self.env["product.product"].search(
                    [
                        (
                            "property_contract_template_id",
                            "=",
                            record.contract_template_id.id,
                        )
                    ],
                    limit=1,
                )
                if rel_product:
                    record.service_pack_id = rel_product.id

    def set_close_status_type_by_date(self):
        if self.date_end.strftime("%Y-%m-%d") == datetime.now().strftime("%Y-%m-%d"):
            self.write({"status": "closed"})
        else:
            self.write({"status": "closed_planned"})

    def action_activate_contract(self):
        return self._action_contract("activate")

    def action_close_contract(self):
        return self._action_contract("close")

    def action_modify_contract(self):
        return self._action_contract("modification")

    def _action_contract(self, action):
        self.ensure_one()
        wizard = self.env["service.invoicing.action.wizard"].create(
            {"service_invoicing_id": self.id, "executed_action": action}
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Executing: {}").format(action),
            "res_model": "service.invoicing.action.wizard",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }

    @api.model
    def cron_close_todays_closed_planned_contacts(self):
        impacted_contracts = self.env["contract.contract"].search(
            [("status", "closed_planned")]
        )
        for contract in impacted_contracts:
            contract.set_close_status_type_by_date()
        return True
