from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)


class ContractGenerationWizard(models.TransientModel):
    _name = "energy_selfconsumption.contract_generation.wizard"
    _description = "Service to generate contract"

    selfconsumption_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption", readonly=True
    )
    start_date = fields.Date(
        string="Start date",
        help="Starting date of the invoicing",
        required=True,
        default=fields.Date.today(),
    )
    payment_mode = fields.Many2one(
        "account.payment.mode",
        string="Payment mode",
        default=lambda self: self._default_payment_mode(),
    )

    def _default_payment_mode(self):
        return self.env["account.payment.mode"].search(
            [("company_id", "=", self.env.company.id), ("payment_type", "=", "inbound")]
        )

    def _get_impacted_sale_orders(self):
        sale_orders = self.selfconsumption_id.get_sale_orders()
        return sale_orders.filtered(lambda so: so.state == "draft")

    def action_generate_contracts(self):
        # Get distribution table
        distribution_id = (
            self.selfconsumption_id.distribution_table_ids.filtered_domain(
                [("state", "=", "process")]
            )
        )
        if not distribution_id:
            raise ValidationError(
                _("There is no distribution table in proces of activation.")
            )
        # Iterate trough sale orders and:
        for sale_order in self._get_impacted_sale_orders():
            # 1.-confirm sale order
            so_extra = {
                "commitment_date": self.start_date,
                "payment_mode_id": self.payment_mode.id,
            }
            with sale_order_utils(self.env, sale_order) as component:
                contract = component.confirm(**so_extra)
            # 2.- setup contract line description
            self.selfconsumption_id._setup_selfconsumption_contract_line_description(
                distribution_id, contract
            )
            # 3.- setup contract line main_line
            contract.contract_line_ids[0].write({"main_line": True})
            # 4.- mark contract as active
            with contract_utils(self.env, contract) as component:
                component.set_contract_status_active(self.start_date)
        # 5.- mark project as active
        self.selfconsumption_id.write(
            {"payment_mode_id": self.payment_mode.id, "state": "active"}
        )
        #  6.- mark distribution table as active
        self.selfconsumption_id.distribution_table_state("process", "active")
        return True
