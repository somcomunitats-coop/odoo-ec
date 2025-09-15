import logging

from odoo import SUPERUSER_ID, _, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Creating Selfconsumption journal for companies")
    companies = env["res.company"].search([])
    for company in companies:
        if company.hierarchy_level == "community":
            selfconsumption_product_categ = env.ref(
                "energy_selfconsumption.product_category_selfconsumption_pack"
            )
            selfconsumption_journal = env["account.journal"].search(
                [("code", "=", "AFC"), ("company_id", "=", company.id)]
            )
            if (
                selfconsumption_journal
                and not selfconsumption_product_categ.with_company(
                    company
                ).service_invoicing_sale_journal_id
            ):
                selfconsumption_product_categ.with_company(company).write(
                    {"service_invoicing_sale_journal_id": selfconsumption_journal.id}
                )
            if not selfconsumption_journal:
                account_ref = "l10n_es.{}_account_common_7050"
                account = env.ref(account_ref.format(company.id))
                selfconsumption_journal = env["account.journal"].create(
                    {
                        "name": "Autoconsumo Fotovoltaico Compartido",
                        "type": "sale",
                        "company_id": company.id,
                        "default_account_id": account.id,
                        "refund_sequence": True,
                        "code": "AFC",
                    }
                )
                if not selfconsumption_product_categ.with_company(
                    company
                ).service_invoicing_sale_journal_id:
                    selfconsumption_product_categ.with_company(company).write(
                        {
                            "service_invoicing_sale_journal_id": selfconsumption_journal.id
                        }
                    )
    _logger.info("Migration completed.")
