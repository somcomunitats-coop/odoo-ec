from . import components
from . import models
from . import tests
from . import wizards

import logging
from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)


def post_setup_intercompany_invoicing_config(cr, registry):
    logger.info("Running Inter company setup")
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([])
    for company in companies:
        company.write({"invoice_auto_validation": False})
    logger.info(
        "Inter company invoice auto validation disabled by default on all companies."
    )
