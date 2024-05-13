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

    instance_crm_team = env.ref("sales_team.team_sales_department")
    instance_crm_team.write({"is_default_team": True})

    # auto reference existing stages
    existing_stages = env["crm.stage"].sudo().search([])
    for stage in existing_stages:
        stage.sudo().write(
            {"team_id": instance_crm_team.id, "original_stage_id": stage.id}
        )

    # create stages for existing sale teams
    existing_sale_teams = env["crm.team"].sudo().search([])
    for sale_team in existing_sale_teams:
        if sale_team.id != instance_crm_team.id:
            default_stages = env["crm.stage"].get_create_default_stages(
                sale_team.company_id
            )
            for stage in default_stages:
                stage.sudo().copy(
                    {
                        "original_stage_id": stage.id,
                        "team_id": sale_team.id,
                    }
                )

    # create missing stages/sale_teams for all companies
    companies = env["res.company"].sudo().search([])
    for company in companies:
        default_team = env["crm.team"].get_create_default_sale_team(company)
        default_stages = env["crm.stage"].get_create_default_stages(company)
        for default_stage in default_stages:
            default_stage.sudo().write({"team_id": default_team.id})

    # setup stages/sale_teams for leads
    existing_leads = env["crm.lead"].sudo().search([])
    for lead in existing_leads:
        default_team = env["crm.team"].get_create_default_sale_team(lead.company_id)
        # we want to setup team_id on all leads except the ones belonging to the existing  ones custom created
        custom_existing_sale_team_ids = existing_sale_teams.mapped("id")
        custom_existing_sale_team_ids.remove(instance_crm_team.id)
        l_w_dict = {}
        if lead.team_id.id not in custom_existing_sale_team_ids:
            lead_team = default_team
            l_w_dict["team_id"] = default_team.id
        else:
            lead_team = lead.team_id
            # lead.write({"team_id": default_team.id})
        # the lead belongs to a stage that doesn't correspond. Look for the related one.
        if lead.stage_id.team_id.id != lead_team.id:
            new_stage = (
                env["crm.stage"]
                .sudo()
                .search(
                    [
                        ("team_id", "=", lead_team.id),
                        ("original_stage_id", "=", lead.stage_id.id),
                    ]
                )
            )
            if not new_stage:
                new_stage = lead.stage_id.sudo().copy(
                    {
                        "original_stage_id": lead.stage_id.id,
                        "team_id": lead_team.id,
                    }
                )
            else:
                new_stage = new_stage[0]
            l_w_dict["stage_id"] = new_stage.id
        if l_w_dict:
            lead.write(l_w_dict)

    logger.info("Migration applied to tags, teams and leads on crm")
