import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)


def migrate(cr, version):
    logger.info("Running post migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})

    companies = env["res.company"].search([])
    category_member = env.ref("cooperator.product_category_company_share")
    category_member_associations = env.ref(
        "energy_communities.product_category_share_recurring_fee_pack"
    )
    category_invited = env.ref(
        "energy_communities_cooperator.product_category_company_invited_share"
    )
    category_voluntary = env.ref(
        "energy_communities_cooperator.product_category_company_voluntary_share"
    )

    for company in companies:
        category_member.with_company(company).product_website = False
        category_member_associations.with_company(company).product_website = False
        category_invited.with_company(company).product_website = False
        category_voluntary.with_company(company).product_website = True

        category_member.with_company(company).product_qty_must_be_read_only = True
        category_member_associations.with_company(
            company
        ).product_qty_must_be_read_only = True
        category_invited.with_company(company).product_qty_must_be_read_only = True
        category_voluntary.with_company(company).product_qty_must_be_read_only = False
