import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)


def migrate(cr, version):
    logger.info("Running post migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})

    invited_category = env.ref(
        "energy_communities_cooperator.product_category_company_invited_share"
    )

    companies = env["res.company"].search([])

    for company in companies:
        invited_product = env["product.template"].search(
            [("categ_id", "=", invited_category.id)], limit=1
        )
        if not invited_product:
            raise ValueError("Invited product not found")

        partners = env["res.partner"].search(
            [
                ("company_id", "=", company.id),
                ("no_member_autorized_in_energy_actions", "=", True),
            ]
        )
        for partner in partners:
            cooperator = (
                env["cooperative.membership"]
                .sudo()
                .search(
                    [
                        ("company_id", "=", company.id),
                        ("partner_id", "=", partner.id),
                        ("member", "=", True),
                    ]
                )
            )
            if not cooperator:
                env["cooperative.membership"].sudo().create(
                    {
                        "company_id": company.id,
                        "partner_id": partner.id,
                        "share_ids": [
                            (
                                0,
                                0,
                                {
                                    "share_product_id": invited_product.id,
                                    "share_number": 1,
                                },
                            ),
                        ],
                    }
                )
