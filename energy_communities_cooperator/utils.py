from odoo.api import Environment

from odoo.addons.energy_communities.utils import _get_component


@contextmanager
def subscription_request_utils(
    env: Environment,
    subscription_request: None,
) -> Component:
    yield _get_component(
        env, "subscription.request", "subscription.request.utils", subscruption_request
    )
