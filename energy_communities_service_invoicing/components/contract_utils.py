from odoo.addons.component.core import Component


class ContractUtils(Component):
    _inherit = "contract.utils"

    def setup_initial_data(self):
        self._set_configuration_journal_if_defined()
        self._set_start_date(self.work.record.sale_order_id.commitment_date)
        if "discount" in self.work.record.sale_order_id.metadata_line_ids.mapped("key"):
            self._set_discount(
                self.work.record.sale_order_id.get_metadata_value("discount")
            )
        contract_update_dict = {"status": "paused"}
        for contract_update_data in self.work.record.sale_order_id.metadata_line_ids:
            if contract_update_data.key not in ["discount"]:
                value = contract_update_data.value
                # TODO: Not a very robust condition. Assuming all Many2one fields are defined with _id at the end
                if "_id" in contract_update_data.key:
                    value = int(contract_update_data.value)
                contract_update_dict[contract_update_data.key] = value
        for line in self.work.record.contract_line_ids:
            line.write(
                {
                    "ordered_qty_type": line.qty_type,
                    "ordered_quantity": line.quantity,
                    "ordered_qty_formula_id": line.qty_formula_id.id,
                    "qty_type": "fixed",
                    "quantity": 0,
                }
            )
        self.work.record.write(contract_update_dict)

    def _set_start_date(self, date_start):
        self.work.record.write({"date_start": date_start})
        for line in self.work.record.contract_line_ids:
            line.write({"date_start": date_start})
            line._compute_state()

    def _set_discount(self, discount):
        for line in self.work.record.contract_line_ids:
            line.write({"discount": discount})

    # method to be extended if using component for another pack_type
    def _set_configuration_journal_if_defined(self):
        if self.work.record.pack_type == "platform_pack":
            journal_id = self.work.record.company_id.service_invoicing_sale_journal_id
            if journal_id:
                self.work.record.write({"journal_id": journal_id.id})

    def _activate_contract_lines(self, execution_date):
        for line in self.work.record.contract_line_ids:
            line.write(
                {
                    "date_start": execution_date,
                    "next_period_date_start": execution_date,
                    "recurring_next_date": execution_date,
                    "last_date_invoiced": None,
                    "qty_type": line.ordered_qty_type,
                    "quantity": line.ordered_quantity,
                    "qty_formula_id": line.ordered_qty_formula_id.id,
                }
            )
            line._compute_state()

    def set_contract_status_active(self, execution_date):
        self._activate_contract_lines(execution_date)
        self._set_start_date(execution_date)
        self.work.record.write({"status": "in_progress"})

    def set_contract_status_closed(self, execution_date):
        for line in self.work.record.contract_line_ids:
            if self.work.record.status == "paused" or self.work.record.is_free_pack:
                self._activate_contract_lines(execution_date)
            line.write({"date_end": execution_date})
            line._compute_state()
        self.work.record.set_close_status_type_by_date()

    def clean_non_service_lines(self):
        for line in self.work.record.contract_line_ids:
            if not self._is_service_line(line):
                line.cancel()
                line.unlink()

    def modify(
        self,
        execution_date,
        executed_modification_action,
        pricelist_id=None,
        pack_id=None,
        discount=None,
        payment_mode_id=None,
    ):
        initial_status = self.work.record.status
        # TODO: control closing date in order to being able modify contract with previous date.
        # on contract line:
        # skip last_date_invoice validation for modification action if contract is ready to start or active on free plan.
        self.set_contract_status_closed(execution_date)
        sale_order_utils = self.component(
            usage="sale.order.utils", model_name="sale.order"
        )
        new_service_invoicing_id = sale_order_utils.create_service_invoicing_initial(
            **self._build_service_invoicing_params(
                "modification",
                executed_modification_action,
                execution_date,
                pricelist_id,
                pack_id,
                discount,
                payment_mode_id,
            )
        )
        # TODO:
        # Do we really want new contract to be in_progress on a modification??
        # if initial_status == "in_progress" and not self.work.record.is_free_pack:
        #     self.set_contract_status_active()
        self._setup_successors_and_predecessors(new_service_invoicing_id)
        return new_service_invoicing_id

    def reopen(
        self,
        execution_date,
        pricelist_id=None,
        pack_id=None,
        discount=None,
        payment_mode_id=None,
    ):
        self.set_contract_status_closed(execution_date)
        new_service_invoicing_id = self.component(
            usage="sale.order.utils", model_name="sale.order"
        ).create_service_invoicing_initial(
            **self._build_service_invoicing_params(
                "reopen",
                "modify_pack,modify_pricelist,modify_discount,modify_payment_mode",
                execution_date,
                pricelist_id,
                pack_id,
                discount,
                payment_mode_id,
            )
        )
        self._setup_successors_and_predecessors(new_service_invoicing_id)
        return new_service_invoicing_id

    def _build_service_invoicing_params(
        self,
        executed_action,
        executed_action_description,
        execution_date,
        pricelist_id=None,
        pack_id=None,
        discount=None,
        payment_mode_id=None,
    ):
        executed_action_description_list = executed_action_description.split(",")
        return {
            "company_id": self.work.record.partner_id.related_company_id,
            "pack_id": pack_id
            if "modify_pack" in executed_action_description_list
            else self.work.record.pack_id,
            "pricelist_id": pricelist_id
            if "modify_pricelist" in executed_action_description_list
            else self.work.record.pricelist_id,
            "payment_mode_id": payment_mode_id
            if "modify_payment_mode" in executed_action_description_list
            else self.work.record.payment_mode_id,
            "start_date": execution_date,
            "executed_action": executed_action,
            "executed_action_description": executed_action_description,
            "metadata": {
                "community_company_id": self.work.record.community_company_id.id
                if self.work.record.community_company_id
                else False,
                "discount": discount
                if "modify_discount" in executed_action_description_list
                else self.work.record.discount,
            },
        }

    def _is_service_line(self, contract_line):
        if self.work.record.contract_template_id:
            contract_template_services = (
                self.work.record.contract_template_id.contract_line_ids.mapped(
                    "product_id"
                )
            )
            return contract_line.product_id in contract_template_services
        return False

    def _setup_successors_and_predecessors(self, new_service_invoicing_id):
        self.work.record.write({"successor_contract_id": new_service_invoicing_id.id})
        new_service_invoicing_id.write({"predecessor_contract_id": self.work.record.id})
