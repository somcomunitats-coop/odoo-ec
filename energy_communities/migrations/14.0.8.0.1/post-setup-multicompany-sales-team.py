import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)
from odoo.exceptions import UserError


def migrate(cr, version):
    logger.info("Running post sales team migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].sudo().search([])
    lead_count = 0
    for company in companies:
        if company.hierarchy_level != "instance":
            existing_team = (
                env["crm.team"].sudo().search([("company_id", "=", company.id)])
            )
            if not existing_team:
                existing_team = (
                    env["crm.team"]
                    .sudo()
                    .create(
                        {
                            "name": company.name,
                            "use_opportunities": True,
                            "company_id": company.id,
                        }
                    )
                )
                related_leads = (
                    env["crm.lead"].sudo().search([("company_id", "=", company.id)])
                )
                for lead in related_leads:
                    lead.write({"team_id": existing_team.id})
                    lead_count += 1
    logger.info("Migration applied to {} leads".format(lead_count))
