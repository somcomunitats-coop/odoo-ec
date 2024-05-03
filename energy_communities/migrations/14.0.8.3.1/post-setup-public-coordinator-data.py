import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)
from odoo.exceptions import UserError


def migrate(cr, version):
    logger.info("Running post migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("hierarchy_level", "=", "coordinator")])
    for company in companies:
        company.action_create_odoo_landing()
    logger.info("Migration applied to {} companies".format(len(companies)))
