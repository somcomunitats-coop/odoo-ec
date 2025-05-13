from odoo import _
from odoo.api import Environment
from odoo.exceptions import ValidationError

from odoo.addons.contract.models.contract import ContractContract

PACK_VALUES = [
    ("platform_pack", _("Platform Pack")),
    ("none", _("None")),
]

PAUSED = "paused"
IN_PROGRESS = "in_progress"
CLOSED_PLANNED = "closed_planned"
CLOSED = "closed"
_CONTRACT_STATUS_VALUES = [
    (PAUSED, _("Paused")),
    (IN_PROGRESS, _("In progress")),
    (CLOSED_PLANNED, _("Planned closure")),
    (CLOSED, _("Closed")),
]

ACTIVATE = "activate"
MODIFICATION = "modification"
REOPEN = "reopen"
CLOSE = "close"
_SERVICE_INVOICING_EXECUTED_ACTION_VALUES = [
    (ACTIVATE, _("Activate")),
    (MODIFICATION, _("Modification")),
    (REOPEN, _("Reopen")),
    (CLOSE, _("Close")),
]
_SALE_ORDER_SERVICE_INVOICING_ACTION_VALUES = [
    ("none", _("None"))
] + _SERVICE_INVOICING_EXECUTED_ACTION_VALUES[:-1]


def service_invoicing_tree_view(env: Environment):
    return {
        "name": _("Service Contracts"),
        "view_type": "tree",
        "view_mode": "tree,form",
        "views": [
            (
                env.ref(
                    "energy_communities_service_invoicing.view_service_invoicing_tree"
                ).id,
                "tree",
            ),
            (
                env.ref(
                    "energy_communities_service_invoicing.view_contract_contract_customer_form_platform_admin"
                ).id,
                "form",
            ),
        ],
        "res_model": "contract.contract",
        "context": env["contract.contract"].get_service_invoicing_views_context(),
        "domain": env["contract.contract"].get_service_invoicing_views_domain(),
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
def raise_existing_same_open_platform_pack_contract_error(existing_contract):
    raise ValidationError(
        _(
            "It already exists an open contract ({}) with same company and community."
        ).format(existing_contract.name)
    )


def get_existing_open_pack_contract(
    env, partner_id, pack_type, contract_id=False, custom_query=False
):
    # ("community_company_id", "=", community_company_id.id),
    query = [
        ("partner_id", "=", partner_id.id),
        ("pack_type", "=", pack_type),
        ("status", "in", ["paused", "in_progress"]),
    ]
    if contract_id:
        query.append(("id", "!=", contract_id.id))
    if custom_query:
        query = custom_query + query
    return env["contract.contract"].search(query, limit=1)


def get_existing_last_closed_pack_contract(
    env, partner_id, community_company_id, contract_id=False
):
    query = [
        ("partner_id", "=", partner_id.id),
        ("community_company_id", "=", community_company_id.id),
        ("pack_type", "=", "platform_pack"),
        ("status", "in", ["closed_planned", "closed"]),
        ("successor_contract_id", "=", False),
    ]
    if contract_id:
        query.append(("id", "!=", contract_id.id))
    return env["contract.contract"].search(query, limit=1)


def get_existing_pack_contract(
    env,
    partner_id,
    pack_type,
    status,
    extra_query=False,
    successor_contract_id=False,
    contract_id=False,
):
    query = [
        ("partner_id", "=", partner_id.id),
        ("pack_type", "=", pack_type),
        ("status", "in", status),
        ("successor_contract_id", "=", successor_contract_id),
    ]
    if extra_query:
        query = extra_query + query
    if contract_id:
        query.append(("id", "!=", contract_id.id))
    return env["contract.contract"].search(query, limit=1)
