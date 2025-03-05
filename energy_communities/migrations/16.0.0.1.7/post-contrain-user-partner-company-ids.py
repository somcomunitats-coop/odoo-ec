import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)


def migrate(cr, version):
    logger.info("Running post migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})
    # equalize company_ids
    users = env["res.users"].search([])
    for user in users:
        user.constrains_user_partner_id_company_ids()
