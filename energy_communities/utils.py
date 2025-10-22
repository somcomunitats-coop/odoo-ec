from contextlib import contextmanager
from typing import Any

from odoo.api import Environment
from odoo.tools.translate import code_translations

from odoo.addons.base.models.res_users import Users
from odoo.addons.component.core import Component, WorkContext
from odoo.addons.contract.models.contract import ContractContract
from odoo.addons.product.models.product_template import ProductTemplate
from odoo.addons.sale.models.sale_order import SaleOrder


def _get_component(
    env: Environment,
    model_name: str,
    usage: str,
    record: Any = None,
    use_sudo: bool = False,
) -> Component:
    backend = env["utils.backend"].browse(1)
    work = WorkContext(
        model_name=model_name, collection=backend, record=record, use_sudo=use_sudo
    )
    return work.component(usage=usage)


@contextmanager
def user_creator(
    env: Environment,
) -> Component:
    yield _get_component(env, "res.users", "user.create")


@contextmanager
def user_role_utils(
    env: Environment, user_id: Users, use_sudo: bool = False
) -> Component:
    yield _get_component(
        env, "res.users", "user.role.utils", user_id, use_sudo=use_sudo
    )


@contextmanager
def account_utils(
    env: Environment,
    use_sudo: bool = False,
) -> Component:
    yield _get_component(
        env, "account.chart.template", "account.utils", use_sudo=use_sudo
    )


@contextmanager
def contract_utils(
    env: Environment,
    contract_id: ContractContract,
) -> Component:
    yield _get_component(env, "contract.contract", "contract.utils", contract_id)


@contextmanager
def product_utils(
    env: Environment,
    product_template_id: ProductTemplate = None,
    use_sudo: bool = False,
) -> Component:
    yield _get_component(
        env, "product.template", "product.utils", product_template_id, use_sudo=use_sudo
    )


@contextmanager
def sale_order_utils(
    env: Environment,
    sale_order_id: SaleOrder = None,
) -> Component:
    yield _get_component(env, "sale.order", "sale.order.utils", sale_order_id)


def get_translation(source, lang, mods):
    translation = code_translations.get_web_translations(mods, lang)
    translation.update(code_translations.get_python_translations(mods, lang))
    return translation.get(source, source)


def get_successful_popup_message(title, message):
    return {
        "type": "ir.actions.client",
        "tag": "display_notification",
        "params": {
            "type": "success",
            "title": title,
            "message": message,
            "sticky": False,
            "next": {"type": "ir.actions.act_window_close"},
        },
    }
