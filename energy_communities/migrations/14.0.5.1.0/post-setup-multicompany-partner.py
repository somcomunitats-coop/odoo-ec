import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)
from odoo.exceptions import UserError


def migrate(cr, version):
    logger.info("Running post migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("hierarchy_level", "!=", "instance")])
    for company in companies:
        if company.hierarchy_level == "coordinator":
            # apply to new company-partner all visible companies (company_ids)
            company.partner_id.write(
                {
                    "company_ids": [
                        (4, env.ref("base.main_company").id),
                        (4, company.id),
                    ]
                }
            )
        if company.hierarchy_level == "community":
            # apply to company-partner all visible companies (company_ids)
            community_company_ids = [
                (4, env.ref("base.main_company").id),
                (4, company.id),
            ]
            if company.parent_id:
                community_company_ids.append((4, company.parent_id.id))
            company.partner_id.write({"company_ids": community_company_ids})
            # apply company to coordinator-partner visible companies (company_ids)
            company.parent_id.partner_id.write(
                {
                    "company_ids": [
                        (4, company.id),
                    ]
                }
            )
    logger.info("Migration applied to {} companies".format(len(companies)))
