from datetime import datetime

from dateutil.parser import parse

from odoo import _
from odoo.api import Environment
from odoo.exceptions import ValidationError

from odoo.addons.contract.models.contract import ContractContract
from odoo.addons.energy_communities.config import PACK_TYPE_PLATFORM

from .config import (
    CONTRACT_STATUS_CLOSED,
    CONTRACT_STATUS_CLOSED_PLANNED,
    CONTRACT_STATUS_IN_PROGRESS,
    CONTRACT_STATUS_PAUSED,
)


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
        ("status", "in", [CONTRACT_STATUS_PAUSED, CONTRACT_STATUS_IN_PROGRESS]),
    ]
    if contract_id:
        query.append(("id", "!=", contract_id.id))
    if custom_query:
        query = custom_query + query
    return env["contract.contract"].search(query, limit=1)


def get_existing_last_closed_platform_pack_contract(
    env, partner_id, community_company_id, contract_id=False
):
    query = [
        ("partner_id", "=", partner_id.id),
        ("community_company_id", "=", community_company_id.id),
        ("pack_type", "=", PACK_TYPE_PLATFORM),
        ("status", "in", [CONTRACT_STATUS_CLOSED_PLANNED, CONTRACT_STATUS_CLOSED]),
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


def get_monthdays_selection_options():
    day_list = []
    for i in range(1, 31):
        day_list.append((f"{i:02}", f"{i:02}"))
    return day_list


def get_month_selection_options():
    return [
        ("01", "January"),
        ("02", "February"),
        ("03", "March"),
        ("04", "April"),
        ("05", "May"),
        ("06", "June"),
        ("07", "July"),
        ("08", "August"),
        ("09", "September"),
        ("10", "October"),
        ("11", "November"),
        ("12", "December"),
    ]


def validate_monthday_date(month, day):
    if month and day:
        try:
            parse(str(datetime.now().year) + "-" + month + "-" + day)
        except Exception as e:
            raise ValidationError(e.args[0] % e.args[1])
    return True

