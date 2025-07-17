import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)
from odoo.exceptions import UserError


def _compute_pack_type_on_models(env):
    product_categories = env["product.category"].search([])
    for product_category in product_categories:
        product_category._compute_pack_type()
    product_templates = env["product.template"].search([])
    for product_template in product_templates:
        product_template._compute_pack_type()
    contract_templates = env["contract.template"].search([])
    for contract_template in contract_templates:
        contract_template._compute_pack_type()
    contracts = env["contract.template"].search([])
    for contract in contracts:
        contract._compute_pack_type()
    invoices = env["account.move"].search([("move_type", "=", "out_invoice")])
    for invoice in invoices:
        invoice._compute_pack_type()


def _compute_product_category_flags(env):
    product_categories = env["product.category"].search([])
    for product_category in product_categories:
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
    _compute_pack_type_on_models(env)
    _compute_product_category_flags(env)
    _create_companies_config_tariff(env)
    logger.info("Post migration {} executed".format(version))
