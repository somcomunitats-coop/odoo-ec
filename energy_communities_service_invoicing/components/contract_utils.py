from odoo.addons.component.core import Component

_RECURRENCY_VALUES_SETUP = {
    "recurring_interval": int,
    "recurring_rule_type": str,
    "recurring_invoicing_type": str,
    "recurring_rule_mode": str,
    "recurring_invoicing_fixed_type": str,
    "fixed_invoicing_day": str,
    "fixed_invoicing_month": str,
    "recurring_next_date": str,
    "next_period_date_start": str,
}

_RECURRENCY_VALUES = _RECURRENCY_VALUES_SETUP | {"last_date_invoiced": str}


class ContractUtils(Component):
    _inherit = "contract.utils"

    def activate(self, execution_date):
        self._activate_contract_lines(execution_date)
        self.propagate_recurrency_values_to_contract()
        self.work.record.write({"status": "in_progress"})

    def close(self, execution_date):
        for line in self.work.record.contract_line_ids:
            if self.work.record.status == "paused" or self.work.record.is_free_pack:
                self._activate_contract_lines(execution_date)
            line.write({"date_end": execution_date})
            line._compute_state()
        self.propagate_recurrency_values_to_contract()
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
        self.close(execution_date)
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
        self.propagate_recurrency_values_to_contract(new_service_invoicing_id)
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
        self.propagate_recurrency_values_to_contract(new_service_invoicing_id)
        self._setup_successors_and_predecessors(new_service_invoicing_id)
        return new_service_invoicing_id

    def _activate_contract_lines(self, execution_date):
        self.work.record.write({"date_start": execution_date})
        for line in self.work.record.contract_line_ids:
            line_dict = {
                "date_start": execution_date,
                "qty_type": line.ordered_qty_type,
                "quantity": line.ordered_quantity,
                "qty_formula_id": line.ordered_qty_formula_id.id,
            }
            line.write(line_dict)
            line._compute_state()

    # this method is meant to be used by sale_order_utils_component on sale order confirmation (contract creation).
    def initial_setup(self):
        self._clean_non_service_lines()
        self._setup_contract_values()
        self._activate_contract_if_is_free()

    def _clean_non_service_lines(self):
        for line in self.work.record.contract_line_ids:
            if not self._is_service_line(line):
                line.cancel()
                line.unlink()

    def _setup_contract_values(self):
        metadata_keys_arr = self.work.record.sale_order_id.metadata_line_ids.mapped(
            "key"
        )
        self._set_discount_if_needed(metadata_keys_arr)
        self._set_lines_initial_values()
        self._set_contract_recurrency(metadata_keys_arr)
        self._set_config_journal()
        self._set_resting_metadata_in_contract(metadata_keys_arr)
        self.propagate_recurrency_values_to_contract()

    def _activate_contract_if_is_free(self):
        # Important! We activate by default free packs
        if self.work.record.is_free_pack:
            self.activate(self.work.record.sale_order_id.commitment_date)

    def _set_lines_initial_values(self):
        for line in self.work.record.contract_line_ids:
            line_params = {
                "date_start": self.work.record.date_start,
                "ordered_qty_type": line.qty_type,
                "ordered_quantity": line.quantity,
                "ordered_qty_formula_id": line.qty_formula_id.id,
                "qty_type": "fixed",
                "quantity": 0,
            }
            if line.product_id.product_tmpl_id.description_sale:
                # context language to be considered from community_company_id or partner_id
                if self.work.record.community_company_id:
                    lang = self.work.record.community_company_id.partner_id.lang
                else:
                    lang = self.work.record.partner_id.lang
                line_params["name"] = line.product_id.product_tmpl_id.with_context(
                    lang=lang
                ).description_sale
            line.write(line_params)

    def _set_discount_if_needed(self, metadata_keys_arr):
        if "discount" in metadata_keys_arr:
            for line in self.work.record.contract_line_ids:
                line.write(
                    {
                        "discount": self.work.record.sale_order_id.get_metadata_value(
                            "discount"
                        )
                    }
                )

    def _set_contract_recurrency(self, metadata_keys_arr):
        recurrence_dict = {}
        for recurrence_key, recurrence_var_type in _RECURRENCY_VALUES.items():
            if recurrence_key in metadata_keys_arr:
                recurrence_dict[recurrence_key] = recurrence_var_type(
                    self.work.record.sale_order_id.get_metadata_value(recurrence_key)
                )
        if recurrence_dict:
            for line in self.work.record.contract_line_ids:
                line.write(recurrence_dict)
                line._compute_state()

        for line in self.work.record.contract_line_ids:
            if line.recurring_rule_mode == "fixed":
                self._recompute_fixed_recurrence_params(line)

    def _set_config_journal(self):
        # config journal
        pack_product = self.env["product.template"].search(
            [
                (
                    "property_contract_template_id",
                    "=",
                    self.work.record.contract_template_id.id,
                )
            ],
            limit=1,
        )
        if pack_product:
            sale_journal_id = pack_product.categ_id.with_company(
                self.work.record.company_id
            ).service_invoicing_sale_journal_id
            if sale_journal_id:
                self.work.record.write({"journal_id": sale_journal_id.id})

    def propagate_recurrency_values_to_contract(self, f_contract=False):
        if not f_contract:
            f_contract = self.work.record
        if f_contract.contract_line_ids:
            update_dict = {}
            for rec_value in _RECURRENCY_VALUES.keys():
                update_dict[rec_value] = getattr(
                    f_contract.contract_line_ids[0], rec_value
                )
            f_contract.write(update_dict)

    def _set_resting_metadata_in_contract(self, metadata_keys_arr):
        # company_id will trigger journal_id recomputation so we must ignore it on any contract write method
        fields_to_ignore = list(_RECURRENCY_VALUES.keys()) + ["discount", "company_id"]
        contract_update_dict = {"status": "paused"}
        for meta_key in metadata_keys_arr:
            if meta_key not in fields_to_ignore:
                metadata_line = (
                    self.work.record.sale_order_id.metadata_line_ids.filtered(
                        lambda meta_line: meta_line.key == meta_key
                    )
                )
                if metadata_line:
                    value = metadata_line.value
                    # TODO: Not a very robust condition. Assuming all Many2one fields are defined with _id at the end
                    # TODO: Problems always when type is not text
                    if "_id" in metadata_line.key:
                        value = int(metadata_line.value)
                    contract_update_dict[meta_key] = value
        self.work.record.write(contract_update_dict)

    def _recompute_fixed_recurrence_params(self, line):
        line._compute_recurring_next_date()

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
        # if metadata defined add them
        if metadata:
            metadata_line_ids = metadata_line_ids | metadata

        # setup new discount if we're modifying discount
        if "modify_discount" in executed_action_description_list:
            metadata_line_ids["discount"] = discount

        # setup recurrency fields from old contract (exclude last_date_invoiced)
        for recurrency_field in _RECURRENCY_VALUES_SETUP.keys():
            if recurrency_field not in metadata_line_ids.keys():
                recurrency_value = getattr(self.work.record, recurrency_field)
                if recurrency_value:
                    metadata_line_ids[recurrency_field] = recurrency_value

        # setup metadata from old sale_order
        for metadata_line in self.work.record.sale_order_id.metadata_line_ids:
            if metadata_line.key not in metadata_line_ids.keys():
                metadata_line_ids[metadata_line.key] = metadata_line.value

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
        return contract_line.product_id.is_pack_service

    def _setup_successors_and_predecessors(self, new_service_invoicing_id):
        self.work.record.write({"successor_contract_id": new_service_invoicing_id.id})
        new_service_invoicing_id.write({"predecessor_contract_id": self.work.record.id})
