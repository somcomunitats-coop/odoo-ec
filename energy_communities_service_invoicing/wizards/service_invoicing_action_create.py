from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)


class ServiceInvoicingActionCreateWizard(models.TransientModel):
    _name = "service.invoicing.action.create.wizard"
    _description = "Create service invoicing for an energy community"

    company_id = fields.Many2one("res.company", string="Coordinator")
    community_company_id = fields.Many2one("res.company", string="Community")
    service_id = fields.Many2one("product.product", string="Service")

    def execute_create(self):
        with sale_order_utils(self.env) as component:
            so = component.create_service_invoicing_activation_sale_order(
                company_id=self.company_id,
                community_company_id=self.community_company_id,
                service_id=self.service_id,
            )
            so.action_confirm()
            rel_contracts = component.get_related_contracts(so)
        with contract_utils(self.env) as component:
            component.set_contract_on_hold(rel_contracts)
        return {
            "type": "ir.actions.act_window",
            "res_model": "contract.contract",
            "views": [
                (
                    self.env.ref(
                        "energy_communities_service_invoicing.view_contract_contract_customer_form"
                    ).id,
                    "form",
                ),
            ],
            "target": "current",
            "res_id": rel_contracts.id,
        }
