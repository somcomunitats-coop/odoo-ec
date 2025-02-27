from odoo import _
from odoo.api import Environment
from odoo.exceptions import ValidationError

from odoo.addons.contract.models.contract import ContractContract

_CONTRACT_STATUS_VALUES = [
    ("paused", _("Paused")),
    ("in_progress", _("In progress")),
    ("closed_planned", _("Planned closure")),
    ("closed", _("Closed")),
]
_SERVICE_INVOICING_EXECUTED_ACTION_VALUES = [
    ("activate", _("Activate")),
    ("modification", _("Modification")),
    ("reopen", _("Reopen")),
    ("close", _("Close")),
]
_SALE_ORDER_SERVICE_INVOICING_ACTION_VALUES = [
    ("none", _("None"))
] + _SERVICE_INVOICING_EXECUTED_ACTION_VALUES[:-1]


def service_invoicing_tree_view(env: Environment):
    # return {
    #     "type": "ir.actions.act_window",
    #     "res_model": "contract.contract",
    #     "views": [
    #         (
    #             env.ref(
    #                 "energy_communities_service_invoicing.view_service_invoicing_tree"
    #             ).id,
    #             "tree",
    #         ),
    #     ],
    #     "target": "current",
    # }

    return {
        # 'name': _('test'),
        "view_type": "tree",
        "view_mode": "tree",
        "view_id": env.ref(
            "energy_communities_service_invoicing.view_service_invoicing_window_platform_manager"
        ).id,
        "res_model": "contract.contract",
        # 'context': "{'type':'out_invoice'}",
        "type": "ir.actions.act_window",
        "target": "current",
    }


def service_invoicing_form_view_for_platform_admins(
    env: Environment, service_invoicing_id: ContractContract
):
    return {
        "type": "ir.actions.act_window",
        "res_model": "contract.contract",
        "views": [
            (
                env.ref(
                    "energy_communities_service_invoicing.view_contract_contract_customer_form_platform_admin"
                ).id,
                "form",
            ),
        ],
        "target": "current",
        "res_id": service_invoicing_id.id,
    }


# TODO: Think a bit more about more about if this 3 methods must go to contract utils component
def raise_existing_same_open_contract_error(existing_contract):
    raise ValidationError(
        _(
            "It already exists an open contract ({}) with same company and community."
        ).format(existing_contract.name)
    )


def get_existing_open_contract(
    env, partner_id, community_company_id, contract_id=False
):
    query = [
        ("partner_id", "=", partner_id.id),
        ("community_company_id", "=", community_company_id.id),
        ("is_pack", "=", True),
        ("status", "in", ["paused", "in_progress"]),
    ]
    if contract_id:
        query.append(("id", "!=", contract_id.id))
    return env["contract.contract"].search(query, limit=1)


def get_existing_last_closed_contract(
    env, partner_id, community_company_id, contract_id=False
):
    query = [
        ("partner_id", "=", partner_id.id),
        ("community_company_id", "=", community_company_id.id),
        ("is_pack", "=", True),
        ("status", "in", ["closed_planned", "closed"]),
        ("successor_contract_id", "=", False),
    ]
    if contract_id:
        query.append(("id", "!=", contract_id.id))
    return env["contract.contract"].search(query, limit=1)
