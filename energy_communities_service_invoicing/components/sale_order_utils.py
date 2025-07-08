from odoo.exceptions import MissingError

from odoo.addons.component.core import Component


class SaleOrderUtils(Component):
    _inherit = "sale.order.utils"

    def create_service_invoicing_sale_order(
        self,
        partner_id,
        pack_id,
        pricelist_id,
        payment_mode_id,
        start_date,
        executed_action,
        executed_action_description,
        metadata,
    ):
        company_id_id = (
            int(metadata["company_id"])
            if "company_id" in metadata
            else self.env.company.id
        )
        so_creation_dict = {
            "partner_id": partner_id.id,
            "company_id": company_id_id,
            "commitment_date": start_date,
            "pricelist_id": pricelist_id.id,
            "service_invoicing_action": executed_action,
            "service_invoicing_action_description": executed_action_description,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": pack_id.product_variant_id.id,
                        "date_start": start_date,
                        "date_end": start_date,
                    },
                )
            ],
        }
        if payment_mode_id:
            so_creation_dict["payment_mode_id"] = payment_mode_id.id
        # Apply configuration sales team to service invoicing sales order
        team_id = pack_id.categ_id.with_context(
            company_id=company_id_id
        ).service_invoicing_sale_team_id
        if team_id:
            so_creation_dict["team_id"] = team_id.id
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
        self.work.record = sale_order

    def create_service_invoicing_initial(
        self,
        partner_id,
        pack_id,
        pricelist_id,
        start_date,
        executed_action,
        executed_action_description="none",
        payment_mode_id=False,
        metadata=False,
    ):
        if not metadata:
            metadata = {}
        self.create_service_invoicing_sale_order(
            partner_id,
            pack_id,
            pricelist_id,
            payment_mode_id,
            start_date,
            executed_action,
            executed_action_description,
            metadata,
        )
        return self.confirm()

    def confirm(self, **so_extra):
        self._validate_sale_order_confirm()
        if so_extra:
            self.work.record.write(so_extra)
        self.work.record.action_confirm()
        with self.collection.work_on(
            "contract.contract", record=self.work.record.service_invoicing_id
        ) as work:
            contract_utils = work.component("contract.utils")
            contract_utils.initial_setup()
            return contract_utils.work.record

    def _validate_sale_order_confirm(self):
        if not self.work.record:
            raise MissingError(
                _("Sale order must be defined in order to confirm it on component")
            )
