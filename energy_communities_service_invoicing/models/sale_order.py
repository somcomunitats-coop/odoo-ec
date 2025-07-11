from odoo import _, api, fields, models

from ..config import (
    SALE_ORDER_SERVICE_INVOICING_ACTION_DEFAULT_VALUE,
    SALE_ORDER_SERVICE_INVOICING_ACTION_VALUES,
)


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"

    service_invoicing_action = fields.Selection(
        selection=SALE_ORDER_SERVICE_INVOICING_ACTION_VALUES,
        required=True,
        string="Service invoicing action",
        default=SALE_ORDER_SERVICE_INVOICING_ACTION_DEFAULT_VALUE,
    )
    service_invoicing_action_description = fields.Char(
        string="Service invoicing action description",
        default=SALE_ORDER_SERVICE_INVOICING_ACTION_DEFAULT_VALUE,
    )
    service_invoicing_id = fields.Many2one(
        "contract.contract",
        string="Related contract",
        compute="_compute_service_invoicing_id",
        store=False,
    )

    def _compute_service_invoicing_id(self):
        for record in self:
            record.service_invoicing_id = False
            contract = self.env["contract.contract"].search(
                [("sale_order_id", "=", record.id)], limit=1
            )
            if contract:
                record.service_invoicing_id = contract.id

    def action_create_contract(self):
        contracts = super().action_create_contract()
        for contract in contracts:
            contract.write(
                {
                    "date_start": self.commitment_date,
                    "pricelist_id": self.pricelist_id.id,
                    "payment_mode_id": self.payment_mode_id.id,
                    "sale_order_id": self.id,
                }
            )
        return contracts

    def action_show_contracts(self):
        self.ensure_one()
        if self.service_invoicing_id:
            action = self.env["ir.actions.act_window"]._for_xml_id(
                "contract.action_customer_contract"
            )
            action.update(
                {
                    "res_id": self.service_invoicing_id.id,
                    "view_mode": "form",
                    "views": filter(lambda view: view[1] == "form", action["views"]),
                }
            )
        return action
