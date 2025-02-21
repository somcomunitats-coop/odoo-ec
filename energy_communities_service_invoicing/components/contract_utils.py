from odoo.addons.component.core import Component


class ContractUtils(Component):
    _inherit = "contract.utils"

    def set_contract_status_ready_to_start(self):
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
        self.work.record.write({"status": "ready_to_start"})

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
        self.set_start_date(execution_date)
        self.work.record.write({"status": "in_progress"})

    def set_contract_status_closed(self, execution_date):
        for line in self.work.record.contract_line_ids:
            if (
                self.work.record.status == "ready_to_start"
                or self.work.record.is_free_pack
            ):
                self._activate_contract_lines(execution_date)
            line.write({"date_end": execution_date})
            line._compute_state()
        self.work.record.set_close_status_type_by_date()

    def set_start_date(self, date_start):
        self.work.record.write({"date_start": date_start})
        for line in self.work.record.contract_line_ids:
            line.write({"date_start": date_start})
            line._compute_state()

    def set_discount(self, discount):
        for line in self.work.record.contract_line_ids:
            line.write({"discount": discount})

    def set_configuration_service_invoicing_journal_if_defined(self):
        journal_id = self.work.record.company_id.service_invoicing_journal_id
        if journal_id:
            self.work.record.write({"journal_id": journal_id.id})

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
        service_pack_id=None,
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
        service_invoicing_params = self._build_service_invoicing_params(
            "modification",
            executed_modification_action,
            execution_date,
            pricelist_id,
            service_pack_id,
            discount,
            payment_mode_id,
        )
        if initial_status == "ready_to_start":
            new_service_invoicing_id = (
                sale_order_utils.create_service_invoicing_ready_to_start(
                    **service_invoicing_params
                )
            )
        if initial_status == "in_progress":
            new_service_invoicing_id = sale_order_utils.create_service_invoicing(
                **service_invoicing_params
            )

        self._setup_successors_and_predecessors(new_service_invoicing_id)
        return new_service_invoicing_id

    def reopen(
        self,
        execution_date,
        pricelist_id=None,
        service_pack_id=None,
        discount=None,
        payment_mode_id=None,
    ):
        self.set_contract_status_closed(execution_date)
        new_service_invoicing_id = self.component(
            usage="sale.order.utils", model_name="sale.order"
        ).create_service_invoicing_ready_to_start(
            **self._build_service_invoicing_params(
                "reopen",
                "modify_service_pack,modify_pricelist,modify_discount,modify_payment_mode",
                execution_date,
                pricelist_id,
                service_pack_id,
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
        service_pack_id=None,
        discount=None,
        payment_mode_id=None,
    ):
        executed_action_description_list = executed_action_description.split(",")
        return {
            "company_id": self.work.record.partner_id.related_company_id,
            "community_company_id": self.work.record.community_company_id,
            "service_pack_id": service_pack_id
            if "modify_service_pack" in executed_action_description_list
            else self.work.record.service_pack_id,
            "pricelist_id": pricelist_id
            if "modify_pricelist" in executed_action_description_list
            else self.work.record.pricelist_id,
            "payment_mode_id": payment_mode_id
            if "modify_payment_mode" in executed_action_description_list
            else self.work.record.payment_mode_id,
            "start_date": execution_date,
            "executed_action": executed_action,
            "executed_action_description": executed_action_description,
            "discount": discount
            if "modify_discount" in executed_action_description_list
            else self.work.record.discount,
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
