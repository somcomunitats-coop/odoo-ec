from odoo.addons.component.core import Component


class ContractUtils(Component):
    _inherit = "contract.utils"

    def set_contract_on_hold(self, contract):
        for line in contract.contract_line_ids:
            line.cancel()

    def set_contract_active(self, contract_id, activation_date):
        for line in contract_id.contract_line_ids:
            line.write(
                {
                    "date_start": activation_date,
                    "next_period_date_start": activation_date,
                    "recurring_next_date": activation_date,
                }
            )
