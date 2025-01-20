from odoo.addons.component.core import Component


class SaleOrderUtils(Component):
    _inherit = "sale.order.utils"

    def create_service_invoicing_activation_sale_order(
        self, company_id, community_company_id, service_id
    ):
        print("CREATE SO on component!")
