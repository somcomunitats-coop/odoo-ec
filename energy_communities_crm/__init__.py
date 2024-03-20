from . import models
from . import controllers
from . import services
from . import wizards
from . import tests

import logging
from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)


def post_setup_multicompany_crm(cr, registry):
    logger.info("Running crm.tag post migration")
    env = api.Environment(cr, SUPERUSER_ID, {})
    tags = env["crm.tag"].search([])
    tag_count = 0
    # convert system tags on not company dependant tags
    for tag in tags:
        if tag.company_id and tag.tag_ext_id:
            tag.write({"company_id": False})
            tag_count += 1
    leads = env["crm.lead"].search([])
    tags_to_analize = []
    # edit tag_ids from leads
    for lead in leads:
        if lead.tag_ids:
            new_tag_ids = []
            for tag in lead.tag_ids:
                if tag.company_id and tag.company_id.id != lead.company_id.id:
                    new_tag_ids.append((3, tag.id))
                    duplicated_tag = env["crm.tag"].search(
                        [
                            ("name", "=", tag.name),
                            ("company_id", "=", lead.company_id.id),
                        ]
                    )
                    if duplicated_tag:
                        new_tag_ids.append((4, duplicated_tag.id))
                    else:
                        new_tag = tag.copy({"company_id": lead.company_id.id})
                        new_tag_ids.append((4, new_tag.id))
                    if tag not in tags_to_analize:
                        tags_to_analize.append(tag)
                else:
                    new_tag_ids.append((4, tag.id))
            lead.write({"tag_ids": new_tag_ids})
    # delete unused tags
    for tag in tags_to_analize:
        existing_lead = env["crm.lead"].search([("tag_ids", "in", tag.id)])
        if not existing_lead:
            tag.unlink()
    # setup sales teams
    instance_crm_team = env.ref("sales_team.team_sales_department")
    instance_crm_team.write({"is_default_team": True})
    companies = env["res.company"].sudo().search([])
    for company in companies:
        if company.hierarchy_level != "instance":
            related_team = env["crm.team"].get_create_sale_team(company)
            related_leads = (
                env["crm.lead"].sudo().search([("company_id", "=", company.id)])
            )
            for lead in related_leads:
                lead.write({"team_id": related_team.id})
    logger.info("Migration applied to tags, teams and leads on crm")
