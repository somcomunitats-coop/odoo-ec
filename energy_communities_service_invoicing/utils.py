from odoo import _
from odoo.api import Environment

from odoo.addons.contract.models.contract import ContractContract

_SERVICE_INVOICING_EXECUTED_ACTION_VALUES = [
    ("activate", _("Activate")),
    ("modification", _("Modification")),
    ("close", _("Close")),
]
_SERVICE_INVOICING_EXECUTED_MODIFICATION_ACTION_VALUES = [
    ("modify_all", _("Modify prices and service pack")),
    ("modify_pricelist", _("Modify prices")),
    ("modify_service_pack", _("Modify service pack")),
]
_SALE_ORDER_SERVICE_INVOICING_ACTION_VALUES = [
    ("none", _("None"))
] + _SERVICE_INVOICING_EXECUTED_ACTION_VALUES[:-1]
_SALE_ORDER_SERVICE_INVOICING_MODIFICATION_ACTION_VALUES = [
    ("none", _("None"))
] + _SERVICE_INVOICING_EXECUTED_MODIFICATION_ACTION_VALUES


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
