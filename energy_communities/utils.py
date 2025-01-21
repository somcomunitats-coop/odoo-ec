from contextlib import contextmanager

from odoo.api import Environment
from odoo.tools.translate import code_translations

from odoo.addons.component.core import Component, WorkContext


def _get_component(env: Environment, model_name: str, usage: str) -> Component:
    backend = env["utils.backend"].browse(1)
    work = WorkContext(
        model_name=model_name,
        collection=backend,
    )
    return work.component(usage=usage)


@contextmanager
def user_creator(
    env: Environment,
) -> Component:
    # backend = env["utils.backend"].browse(1)
    # work = WorkContext(
    #     model_name="res.users",
    #     collection=backend,
    # )
    # yield work.component(usage="user.create")
    yield _get_component(env, "res.users", "user.create")


@contextmanager
def contract_utils(
    env: Environment,
) -> Component:
    # backend = env["utils.backend"].browse(1)
    # work = WorkContext(
    #     model_name="contract.contract",
    #     collection=backend,
    # )
    # yield work.component(usage="contract.utils")
    yield _get_component(env, "contract.contract", "contract.utils")


@contextmanager
def sale_order_utils(
    env: Environment,
) -> Component:
    # backend = env["utils.backend"].browse(1)
    # work = WorkContext(
    #     model_name="sale.order",
    #     collection=backend,
    # )
    # yield work.component(usage="sale.order.utils")
    yield _get_component(env, "sale.order", "sale.order.utils")


def get_translation(source, lang, mods):
    translation = code_translations.get_web_translations(mods, lang)
    translation.update(code_translations.get_python_translations(mods, lang))
    return translation.get(source, source)
