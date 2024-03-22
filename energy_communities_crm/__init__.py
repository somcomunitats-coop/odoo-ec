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
    # setup sales teams and stages
    instance_crm_team = env.ref("sales_team.team_sales_department")
    instance_crm_team.write({"is_default_team": True})
    # create all of them
    companies = env["res.company"].sudo().search([])
    for company in companies:
        default_team = env["crm.team"].get_create_default_sale_team(company)
        default_stages = env["crm.stage"].get_create_default_stages_dict(company)
        for default_stage in default_stages.values():
            default_stage.write({"team_id": default_team.id})
    # setup team and stage for leads (adjust stages if necessary)
    existing_leads = env["crm.lead"].search([])
    for lead in existing_leads:
        # setup team_id for lead
        if not lead.team_id:
            default_team_for_lead = env["crm.team"].get_create_default_sale_team(
                lead.company_id
            )
            lead.write({"team_id": default_team_for_lead.id})
            # TODO: setup properly newly created stages

    # setup stages
    logger.info("Migration applied to tags, teams and leads on crm")
