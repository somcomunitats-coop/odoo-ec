from contextlib import contextmanager

from odoo.api import Environment

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
