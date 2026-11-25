import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Fill the standard participation help on projects that do not have one yet."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    projects = (
        env["energy_selfconsumption.selfconsumption"]
        .with_context(active_test=False)
        .search([])
    )
    _logger.info(
        "Setting the default participation help on %s self-consumption projects.",
        len(projects),
    )
    projects._fill_default_participation_help()
