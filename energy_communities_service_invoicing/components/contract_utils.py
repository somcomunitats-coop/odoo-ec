from odoo.addons.component.core import Component


class ContractUtils(Component):
    _inherit = "contract.utils"

    def set_contract_on_hold(self):
        for line in self.work.record.contract_line_ids:
            line.cancel()

    def set_contract_active(self, activation_date):
        for line in self.work.record.contract_line_ids:
            if self._is_service_line(line):
                line.write(
                    {
                        "date_start": activation_date,
                        "next_period_date_start": activation_date,
                        "recurring_next_date": activation_date,
                        "is_canceled": False,
                    }
                )
                # line.is_cancelled = False
                line._compute_state()

    def _is_service_line(self, contract_line):
        if self.work.record.contract_template_id:
            contract_template_services = (
                self.work.record.contract_template_id.contract_line_ids.mapped(
                    "product_id"
                )
            )
            return contract_line.product_id in contract_template_services
        return False
