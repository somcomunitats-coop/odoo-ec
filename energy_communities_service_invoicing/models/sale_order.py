from odoo import _, api, fields, models

from ..utils import _SALE_ORDER_SERVICE_INVOICING_ACTION_VALUES


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"

    service_invoicing_action = fields.Selection(
        selection=_SALE_ORDER_SERVICE_INVOICING_ACTION_VALUES,
        required=True,
        string="Service invoicing action",
        default="none",
    )
    service_invoicing_action_description = fields.Char(
        string="Service invoicing action description",
        default="none",
    )

    def action_create_contract(self):
        contracts = super().action_create_contract()
        for contract in contracts:
            contract.write(
                {
                    "pricelist_id": self.pricelist_id.id,
                    "payment_mode_id": self.payment_mode_id.id,
                    "sale_order_id": self.id,
                }
            )
        return contracts

    def action_show_contracts(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "contract.action_customer_contract"
        )

        contracts = self.env["contract.contract"].search(
            [("sale_order_id", "=", self.id)]
        )
        if len(contracts) == 1:
            # If there is only one contract, open it directly
            action.update(
                {
                    "res_id": contracts.id,
                    "view_mode": "form",
                    "views": filter(lambda view: view[1] == "form", action["views"]),
                }
            )
        return action
