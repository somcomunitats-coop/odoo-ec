from odoo.addons.component.core import Component
from odoo.addons.energy_communities.utils import contract_utils


class SaleOrderUtils(Component):
    _inherit = "sale.order.utils"

    def create_service_invoicing_sale_order(
        self,
        company_id,
        community_company_id,
        service_pack_id,
        pricelist_id,
        start_date,
        executed_action,
        executed_modification_action,
    ):
        so_creation_dict = {
            "partner_id": company_id.partner_id.id,
            # "company_id": company_id.id,
            "community_company_id": community_company_id.id,
            "pricelist_id": pricelist_id.id,
            "service_invoicing_action": executed_action,
            "service_invoicing_modification_action": executed_modification_action,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": service_pack_id.id,
                        "date_start": start_date,
                        "date_end": start_date,
                    },
                )
            ],
        }
        return self.env["sale.order"].create(so_creation_dict)

    def create_service_invoicing(
        self,
        company_id,
        community_company_id,
        service_pack_id,
        pricelist_id,
        start_date,
        discount,
        executed_action,
        executed_modification_action="none",
    ):
        so = self.create_service_invoicing_sale_order(
            company_id,
            community_company_id,
            service_pack_id,
            pricelist_id,
            start_date,
            executed_action,
            executed_modification_action,
        )
        so.action_confirm()
        service_invoicing_id = self._get_related_contracts(so)
        # TODO: We must call contract_utils with a better component and workcontext modification approach
        with contract_utils(self.env, service_invoicing_id) as component:
            component.clean_non_service_lines()
            component.set_start_date(start_date)
            component.set_discount(discount)
        return service_invoicing_id

    def create_service_invoicing_ready_to_start(
        self,
        company_id,
        community_company_id,
        service_pack_id,
        pricelist_id,
        start_date,
        discount,
        executed_action,
        executed_modification_action="none",
    ):
        service_invoicing_id = self.create_service_invoicing(
            company_id,
            community_company_id,
            service_pack_id,
            pricelist_id,
            start_date,
            discount,
            executed_action,
            executed_modification_action,
        )
        # TODO: We must call contract_utils with a better component and workcontext modification approach
        with contract_utils(self.env, service_invoicing_id) as component:
            component.set_contract_status_ready_to_start()
        return service_invoicing_id

    def _get_related_contracts(self, sale_order):
        return (
            self.env["contract.line"]
            .search([("sale_order_line_id", "in", sale_order.order_line.ids)])
            .mapped("contract_id")
        )
