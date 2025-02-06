from odoo import _
from odoo.api import Environment

from odoo.addons.contract.models.contract import ContractContract

_CONTRACT_STATUS_VALUES = [
    ("ready_to_start", _("Ready to start")),
    ("in_progress", _("In progress")),
    ("closed_planned", _("Planned closure")),
    ("closed", _("Closed")),
]
_SERVICE_INVOICING_EXECUTED_ACTION_VALUES = [
    ("activate", _("Activate")),
    ("modification", _("Modification")),
    ("close", _("Close")),
]
_SALE_ORDER_SERVICE_INVOICING_ACTION_VALUES = [
    ("none", _("None"))
] + _SERVICE_INVOICING_EXECUTED_ACTION_VALUES[:-1]


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
