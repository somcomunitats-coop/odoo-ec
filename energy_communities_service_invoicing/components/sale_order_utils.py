from datetime import datetime

from odoo.addons.component.core import Component


class SaleOrderUtils(Component):
    _inherit = "sale.order.utils"

    def create_service_invoicing_activation_sale_order(
        self, company_id, community_company_id, service_id
    ):
        so_creation_dict = {
            "partner_id": company_id.partner_id.id,
            "community_company_id": community_company_id.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": service_id.id,
                        # "product_uom,qty": 1,
                        "date_start": datetime.now(),
                        "date_end": datetime.now(),
                    },
                )
            ],
        }
        return self.env["sale.order"].create(so_creation_dict)

    def get_related_contracts(self, sale_order):
        return (
            self.env["contract.line"]
            .search([("sale_order_line_id", "in", sale_order.order_line.ids)])
            .mapped("contract_id")
        )
