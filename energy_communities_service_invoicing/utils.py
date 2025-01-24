from odoo.api import Environment

from odoo.addons.contract.models.contract import ContractContract


def service_invoicing_view(env: Environment, service_invoicing_id: ContractContract):
    return {
        "type": "ir.actions.act_window",
        "res_model": "contract.contract",
        "views": [
            (
                env.ref(
                    "energy_communities_service_invoicing.view_contract_contract_customer_form"
                ).id,
                "form",
            ),
        ],
        "target": "current",
        "res_id": service_invoicing_id.id,
    }
