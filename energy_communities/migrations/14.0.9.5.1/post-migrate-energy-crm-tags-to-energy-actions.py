import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)
from odoo.exceptions import UserError


def _get_energy_action_xml_id(ce_tag):
    res = ce_tag.get_external_id()
    tag_ext_id = ""
    tag_ext_id_val = res.get(ce_tag.id)
    if tag_ext_id_val:
        tag_ext_id = tag_ext_id_val
    return tag_ext_id.replace("ce_tag", "energy_action")


def migrate(cr, version):
    logger.info("Running post migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})
    # change metadata values
    cr.execute(
        """
        UPDATE crm_lead_metadata_line
        SET value =  REPLACE(value, 'ce_tag', 'energy_action')
        WHERE key='ce_services';
    """
    )
    # setup energy actions on companies
    companies = env["res.company"].search([])
    for company in companies:
        community_energy_action_ids = [(5, 0, 0)]
        for ce_tag in company.ce_tag_ids:
            xml_id = _get_energy_action_xml_id(ce_tag)
            if xml_id:
                energy_action = env.ref(xml_id)
                if energy_action:
                    community_energy_action_ids.append(
                        (
                            0,
                            0,
                            {
                                "energy_action_id": energy_action.id,
                            },
                        )
                    )
        company.write({"community_energy_action_ids": community_energy_action_ids})
    logger.info("Migration applied to {} companies".format(len(companies)))
