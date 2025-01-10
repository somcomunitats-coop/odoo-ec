from contextlib import contextmanager

from odoo.api import Environment
from odoo.tools.translate import code_translations

from odoo.addons.base.models.res_users import Users
from odoo.addons.component.core import Component, WorkContext


@contextmanager
def user_creator(
    env: Environment,
) -> Component:
    backend = env["utils.backend"].browse(1)
    work = WorkContext(
        model_name="res.users",
        collection=backend,
    )
    yield work.component(usage="user.create")


@contextmanager
def keycloak_utils(
    env: Environment,
    record: Users,
) -> Component:
    backend = env["utils.backend"].browse(1)
    work = WorkContext(model_name="res.users", collection=backend, record=record)
    yield work.component(usage="keycloak")


def get_translation(source, lang, mods):
    translation = code_translations.get_web_translations(mods, lang)
    translation.update(code_translations.get_python_translations(mods, lang))
    return translation.get(source, source)
