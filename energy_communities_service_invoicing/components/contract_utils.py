from odoo.addons.component.core import Component


class ContractUtils(Component):
    _inherit = "contract.utils"

    # TODO: decouple this method into smaller parts
    def _setup_contract_get_update_dict_initial(self):
        self._set_start_date(self.work.record.sale_order_id.commitment_date)
        self._set_lines_ordered_values()
        contract_update_dict = {"status": "paused"}
        # metadata mapping
        metadata_keys_arr = self.work.record.sale_order_id.metadata_line_ids.mapped(
            "key"
        )
        if "discount" in metadata_keys_arr:
            self._set_discount(
                self.work.record.sale_order_id.get_metadata_value("discount")
            )
        recurrence_dict = {}
        if "recurring_interval" in metadata_keys_arr:
            recurrence_dict["recurring_interval"] = int(
                self.work.record.sale_order_id.get_metadata_value("recurring_interval")
            )
        if "recurring_rule_type" in metadata_keys_arr:
            recurrence_dict[
                "recurring_rule_type"
            ] = self.work.record.sale_order_id.get_metadata_value("recurring_rule_type")
        if "recurring_invoicing_type" in metadata_keys_arr:
            recurrence_dict[
                "recurring_invoicing_type"
            ] = self.work.record.sale_order_id.get_metadata_value(
                "recurring_invoicing_type"
            )
        if "last_date_invoiced" in metadata_keys_arr:
            recurrence_dict[
                "last_date_invoiced"
            ] = self.work.record.sale_order_id.get_metadata_value("last_date_invoiced")
        if recurrence_dict:
            self._set_contract_recurrency(**recurrence_dict)
        for contract_update_data in self.work.record.sale_order_id.metadata_line_ids:
            if contract_update_data.key not in [
                "discount",
            ]:
                value = contract_update_data.value
                # TODO: Not a very robust condition. Assuming all Many2one fields are defined with _id at the end
                # TODO: Problems always when type is not text
                if "_id" in contract_update_data.key:
                    value = int(contract_update_data.value)
                contract_update_dict[contract_update_data.key] = value
        return contract_update_dict

    def setup_initial_data(self):
        contract_update_dict = self._setup_contract_get_update_dict_initial()
        self.work.record.write(contract_update_dict)
        self._clean_non_service_lines()
        # TODO: Decide if this must be by design
        if self.work.record.is_free_pack:
            self.set_contract_status_active(
                self.work.record.sale_order_id.commitment_date
            )

    def _clean_non_service_lines(self):
        for line in self.work.record.contract_line_ids:
            if not self._is_service_line(line):
                line.cancel()
                line.unlink()

    def _set_start_date(self, date_start):
        self.work.record.write({"date_start": date_start})
        for line in self.work.record.contract_line_ids:
            line.write({"date_start": date_start})
            line._compute_state()

    def _set_discount(self, discount):
        for line in self.work.record.contract_line_ids:
            line.write({"discount": discount})

    def _set_contract_recurrency(self, **recurrence):
        for line in self.work.record.contract_line_ids:
            if recurrence:
                line.write(recurrence)

    def _set_lines_ordered_values(self):
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

    def _activate_contract_lines(self, execution_date):
        for line in self.work.record.contract_line_ids:
            line_dict = {
                "date_start": execution_date,
                "qty_type": line.ordered_qty_type,
                "quantity": line.ordered_quantity,
                "qty_formula_id": line.ordered_qty_formula_id.id,
            }
            line.write(line_dict)
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
            line.read(["recurring_next_date"])
        self.work.record.set_close_status_type_by_date()

    def modify(
        self,
        execution_date,
        executed_modification_action,
        pricelist_id=None,
        pack_id=None,
        discount=None,
        payment_mode_id=None,
    ):
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
        # initial_status = self.work.record.status
        # if initial_status == "in_progress" and not self.work.record.is_free_pack:
        #     self.set_contract_status_active()
        self._setup_successors_and_predecessors(new_service_invoicing_id)
        return new_service_invoicing_id

    def reopen(
        self,
        execution_date,
        pricelist_id,
        pack_id,
        discount=None,
        payment_mode_id=None,
        metadata=None,
    ):
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
                metadata,
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
        metadata=None,
    ):
        executed_action_description_list = executed_action_description.split(",")
        metadata_line_ids = {}
        if metadata:
            metadata_line_ids = metadata
        else:
            for metadata_line in self.work.record.sale_order_id.metadata_line_ids:
                metadata_line_ids[metadata_line.key] = metadata_line.value
        if "modify_discount" in executed_action_description_list:
            metadata_line_ids["discount"] = discount
        return {
            "partner_id": self.work.record.partner_id,
            "pack_id": pack_id
            if "modify_pack" in executed_action_description_list
            else self.work.record.pack_id,
            "pricelist_id": pricelist_id
            if "modify_pricelist" in executed_action_description_list
            else self.work.record.pricelist_id,  # TODO: This will fail if no pricelist defined on contract
            "payment_mode_id": payment_mode_id
            if "modify_payment_mode" in executed_action_description_list
            else self.work.record.payment_mode_id,
            "start_date": execution_date,
            "executed_action": executed_action,
            "executed_action_description": executed_action_description,
            "metadata": metadata_line_ids,
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
