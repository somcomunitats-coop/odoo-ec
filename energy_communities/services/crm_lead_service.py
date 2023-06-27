import json
import logging
from odoo.addons.component.core import Component
from odoo import _

_logger = logging.getLogger(__name__)


class CRMLeadService(Component):
    _inherit = "crm.lead.service"
    _name = "crm.lead.service"
    _description = """
        CRMLead requests
    """

    def create(self, **params):
        create_dict = super().create(params)
        crm_lead = json.loads(create_dict.response[0].decode("utf-8"))

        metadata = params["metadata"]
        target_source_xml_id = None
        for data in metadata:
            if data["key"] == "source_xml_id":
                target_source_xml_id = data["value"]

        template_external_id = None
        if target_source_xml_id == "ce_source_creation_ce_proposal":
            template_external_id = "email_templ_lead_ce_creation_receipt_confirm_id"
        elif target_source_xml_id == "ce_source_existing_ce_contact":
            template_external_id = "email_templ_lead_request_contact_confirm_id"
        elif target_source_xml_id == "ce_source_existing_ce_info":
            template_external_id = "email_templ_lead_request_ce_news_confirm_id"
        elif target_source_xml_id == "ce_source_future_location_ce_info":
            template_external_id = (
                "email_templ_lead_request_advise_future_ce_confirm_id"
            )
        elif target_source_xml_id == "ce_source_general_info":
            template_external_id = "email_templ_lead_request_platform_news_confirm_id"

        email_values = {"email_to": params["email_from"]}

        if template_external_id:
            template = self.env.ref(
                "energy_communities.{}".format(template_external_id)
            )
            template.sudo().send_mail(crm_lead["id"], email_values=email_values)
            # Add template to chatter message
            self.env["crm.lead"].post_template_to_chatter(template.id)
