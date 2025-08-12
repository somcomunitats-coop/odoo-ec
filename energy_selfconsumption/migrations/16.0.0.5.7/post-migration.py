import logging

from odoo import SUPERUSER_ID, _, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Searching contract lines.")
    contract_lines = env["contract.line"].search([])
    for contract_line in contract_lines:
        _logger.info(f"Updating contract line {contract_line.id}.")
        if contract_line.product_id.product_tmpl_id.description_sale:
            if contract_line.contract_id.community_company_id:
                lang = contract_line.contract_id.community_company_id.partner_id.lang
            else:
                lang = contract_line.contract_id.partner_id.lang
            name = contract_line.product_id.product_tmpl_id.with_context(
                lang=lang
            ).description_sale
            contract_line.write({"name": name})
            _logger.info(f"Updated name contract line {name}.")
        _logger.info("Migration completed.")
