import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)
from odoo.exceptions import UserError


def migrate(cr, version):
    logger.info("Running post migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})
    product_categories = env["product.category"].search([])
    for product_category in product_categories:
        product_category._compute_is_pack()
        product_category._compute_is_pack_service()
        product_category._compute_is_assignable_pack_to_partner()
