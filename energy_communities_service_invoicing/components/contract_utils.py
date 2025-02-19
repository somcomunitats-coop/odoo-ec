from datetime import timedelta

from odoo.addons.component.core import Component


class ContractUtils(Component):
    _inherit = "contract.utils"

    def set_contract_status_ready_to_start(self):
        for line in self.work.record.contract_line_ids:
            line.cancel()
        self.work.record.write({"status": "ready_to_start"})

    def set_contract_status_active(self, execution_date):
        self._uncancel_contract_lines(execution_date)
        self.set_start_date(execution_date)
        self.work.record.write({"status": "in_progress"})

    def set_contract_status_closed(self, execution_date):
        for line in self.work.record.contract_line_ids:
            if self.work.record.status == "ready_to_start":
                self._uncancel_contract_lines(execution_date)
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
    ):
        initial_status = self.work.record.status
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
        self, execution_date, pricelist_id=None, service_pack_id=None, discount=None
    ):
        self.set_contract_status_closed(execution_date)
        new_service_invoicing_id = self.component(
            usage="sale.order.utils", model_name="sale.order"
        ).create_service_invoicing_ready_to_start(
            **self._build_service_invoicing_params(
                "reopen",
                "modify_service_pack,modify_pricelist,modify_discount",
                execution_date,
                pricelist_id,
                service_pack_id,
                discount,
            )
        )
        self._setup_successors_and_predecessors(new_service_invoicing_id)
        return new_service_invoicing_id

    def _build_service_invoicing_params(
        self,
        executed_action,
        executed_modification_action,
        execution_date,
        pricelist_id=None,
        service_pack_id=None,
        discount=None,
    ):
        executed_modification_action_list = executed_modification_action.split(",")
        return {
            "company_id": self.work.record.partner_id.related_company_id,
            "community_company_id": self.work.record.community_company_id,
            "service_pack_id": service_pack_id
            if "modify_service_pack" in executed_modification_action_list
            else self.work.record.service_pack_id,
            "pricelist_id": pricelist_id
            if "modify_pricelist" in executed_modification_action_list
            else self.work.record.pricelist_id,
            "payment_mode_id": self.work.record.payment_mode_id,
            "start_date": execution_date + timedelta(days=1)
            if executed_action == "modification"
            else execution_date,
            "executed_action": executed_action,
            "executed_modification_action": executed_modification_action,
            "discount": discount
            if "modify_discount" in executed_modification_action_list
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

    def _uncancel_contract_lines(self, execution_date):
        for line in self.work.record.contract_line_ids:
            line.write(
                {
                    "date_start": execution_date,
                    "next_period_date_start": execution_date,
                    "recurring_next_date": execution_date,
                    "is_canceled": False,
                }
            )
            line._compute_state()
