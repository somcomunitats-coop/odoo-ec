from odoo.addons.component.core import Component
from odoo.addons.energy_communities.utils import contract_utils


class SaleOrderUtils(Component):
    _inherit = "sale.order.utils"

    def create_service_invoicing_sale_order(
        self,
        company_id,
        community_company_id,
        pack_id,
        pricelist_id,
        payment_mode_id,
        start_date,
        executed_action,
        executed_action_description,
    ):
        so_creation_dict = {
            "partner_id": company_id.partner_id.id,
            # "company_id": company_id.id,
            "community_company_id": community_company_id.id,
            "pricelist_id": pricelist_id.id,
            "service_invoicing_action": executed_action,
            "service_invoicing_action_description": executed_action_description,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": pack_id.id,
                        "date_start": start_date,
                        "date_end": start_date,
                    },
                )
            ],
        }
        if payment_mode_id:
            so_creation_dict["payment_mode_id"] = payment_mode_id.id
        # Apply configuration sales team to service invoicing sales order
        if company_id.service_invoicing_sale_team_id:
            so_creation_dict["team_id"] = company_id.service_invoicing_sale_team_id.id
        sale_order = self.env["sale.order"].create(so_creation_dict)
        # Trigger name computattion in oder to include product's description_sale
        for order_line in sale_order.order_line:
            order_line._compute_name()
        return self.env["sale.order"].create(so_creation_dict)

    def _create_service_invoicing(
        self,
        company_id,
        community_company_id,
        pack_id,
        pricelist_id,
        payment_mode_id,
        start_date,
        discount,
        executed_action,
        executed_action_description="none",
    ):
        so = self.create_service_invoicing_sale_order(
            company_id,
            community_company_id,
            pack_id,
            pricelist_id,
            payment_mode_id,
            start_date,
            executed_action,
            executed_action_description,
        )
        so.action_confirm()
        service_invoicing_id = self._get_related_contracts(so)
        # TODO: We must call contract_utils with a better component and workcontext modification approach
        with contract_utils(self.env, service_invoicing_id) as component:
            component.clean_non_service_lines()
            component.set_start_date(start_date)
            component.set_discount(discount)
            component.set_configuration_service_invoicing_journal_if_defined()
        return service_invoicing_id

    def create_service_invoicing_initial(
        self,
        company_id,
        community_company_id,
        pack_id,
        pricelist_id,
        start_date,
        discount,
        executed_action,
        executed_action_description="none",
        payment_mode_id=False,
    ):
        service_invoicing_id = self._create_service_invoicing(
            company_id,
            community_company_id,
            pack_id,
            pricelist_id,
            payment_mode_id,
            start_date,
            discount,
            executed_action,
            executed_action_description,
        )
        # TODO: We must call contract_utils with a better component and workcontext modification approach
        with contract_utils(self.env, service_invoicing_id) as component:
            component.setup_initial_data()
            if service_invoicing_id.is_free_pack:
                component.set_contract_status_active(start_date)
        return service_invoicing_id

    def _get_related_contracts(self, sale_order):
        return (
            self.env["contract.line"]
            .search([("sale_order_line_id", "in", sale_order.order_line.ids)])
            .mapped("contract_id")
        )
