import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)


def migrate(cr, version):
    logger.info("Running post migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})
    # equalize company_ids
    coop_buttons = env["landing.cooperator.button"].search([])
    for coop_button in coop_buttons:
        if coop_button.visibility != "hidden" and coop_button.mode != "landing_page":
            coop_button.write({"visibility": "map_landing"})
