import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)
from odoo.exceptions import UserError


def _compute_product_category_flags(env):
    product_categories = env["product.category"].search([])
    for product_category in product_categories:
        product_category._compute_is_pack()
        product_category._compute_is_pack_service()
        product_category._compute_is_assignable_pack_to_partner()


def _create_companies_config_tariff(env):
    companies = env["res.company"].search([])
    for company in companies:
        company_pricelist = env["product.pricelist"].create(
            {
                "name": "{} pricelist".format(company.name),
                "currency_id": env.ref("base.EUR").id,
                "company_id": company.id,
            }
        )
        company.write({"pricelist_id": company_pricelist.id})


def migrate(cr, version):
    logger.info("Running post migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})
    _compute_product_category_flags(env)
    _create_companies_config_tariff(env)
    logger.info("Post migration {} executed".format(version))
