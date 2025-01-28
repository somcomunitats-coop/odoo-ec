from datetime import timedelta

from odoo.addons.component.core import Component


class ContractUtils(Component):
    _inherit = "contract.utils"

    def set_contract_on_hold(self):
        for line in self.work.record.contract_line_ids:
            line.cancel()

    def set_contract_active(self, execution_date):
        for line in self.work.record.contract_line_ids:
            if self._is_service_line(line):
                line.write(
                    {
                        "date_start": execution_date,
                        "next_period_date_start": execution_date,
                        "recurring_next_date": execution_date,
                        "is_canceled": False,
                    }
                )
                line._compute_state()

    def set_contract_closed(self, execution_date):
        for line in self.work.record.contract_line_ids:
            if self._is_service_line(line):
                line.write({"date_end": execution_date})
                line._compute_state()

    def set_start_date(self, date_start):
        self.work.record.write({"date_start": date_start})
        for line in self.work.record.contract_line_ids:
            if self._is_service_line(line):
                line.write({"date_start": date_start})
                line._compute_state()

    def modify(
        self,
        execution_date,
        executed_modification_action,
        pricelist_id=None,
        service_pack_id=None,
    ):
        self.set_contract_closed(execution_date)
        sale_order_utils = self.component(
            usage="sale.order.utils", model_name="sale.order"
        )
        new_service_invoicing_id = sale_order_utils.create_service_invoicing(
            self.work.record.company_id,
            self.work.record.community_company_id,
            self._get_service_pack_id()
            if executed_modification_action not in ["modify_all", "modify_service_pack"]
            else service_pack_id,
            self.work.record.pricelist_id
            if executed_modification_action not in ["modify_all", "modify_pricelist"]
            else pricelist_id,
            execution_date + timedelta(days=1),
        )
        self._setup_successors_and_predecessors(new_service_invoicing_id)
        return new_service_invoicing_id

    def _is_service_line(self, contract_line):
        if self.work.record.contract_template_id:
            contract_template_services = (
                self.work.record.contract_template_id.contract_line_ids.mapped(
                    "product_id"
                )
            )
            return contract_line.product_id in contract_template_services
        return False

    def _get_service_pack_id(self):
        for line in self.work.record.contract_line_ids:
            if not self._is_service_line(line):
                return line.product_id
        return False

    def _setup_successors_and_predecessors(self, new_service_invoicing_id):
        self.work.record.write({"successor_contract_id": new_service_invoicing_id.id})
        new_service_invoicing_id.write({"predecessor_contract_id": self.work.record.id})
