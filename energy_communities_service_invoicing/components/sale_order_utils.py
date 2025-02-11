from odoo.addons.component.core import Component
from odoo.addons.energy_communities.utils import contract_utils


class SaleOrderUtils(Component):
    _inherit = "sale.order.utils"

    def _create_service_invoicing_sale_order(
        self,
        company_id,
        pack_id,
        pricelist_id,
        payment_mode_id,
        start_date,
        executed_action,
        executed_action_description,
        metadata,
    ):
        so_creation_dict = {
            "partner_id": company_id.partner_id.id,
            "company_id": self.env.company.id,
            "commitment_date": start_date,
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
        if self.env.company.service_invoicing_sale_team_id:
            so_creation_dict[
                "team_id"
            ] = self.env.company.service_invoicing_sale_team_id.id
        if metadata:
            metadata_list = []
            for meta_key in metadata.keys():
                metadata_list.append(
                    (0, 0, {"key": meta_key, "value": metadata[meta_key]})
                )
            so_creation_dict["metadata_line_ids"] = metadata_list
        sale_order = self.env["sale.order"].create(so_creation_dict)
        # Trigger name computattion in oder to include product's description_sale
        for order_line in sale_order.order_line:
            order_line._compute_name()
        return sale_order

    def create_service_invoicing_initial(
        self,
        company_id,
        pack_id,
        pricelist_id,
        start_date,
        executed_action,
        executed_action_description="none",
        payment_mode_id=False,
        metadata=False,
    ):
        so = self._create_service_invoicing_sale_order(
            company_id,
            pack_id,
            pricelist_id,
            payment_mode_id,
            start_date,
            executed_action,
            executed_action_description,
            metadata,
        )
        so.action_confirm()
        service_invoicing_id = self._get_related_contracts(so)
        # TODO: We must call contract_utils with a better component and workcontext modification approach
        with contract_utils(self.env, service_invoicing_id) as component:
            component.setup_initial_data()
            component.clean_non_service_lines()
            if service_invoicing_id.is_free_pack:
                component.set_contract_status_active(start_date)
        return service_invoicing_id

    def _get_related_contracts(self, sale_order):
        return (
            self.env["contract.line"]
            .search([("sale_order_line_id", "in", sale_order.order_line.ids)])
            .mapped("contract_id")
        )
