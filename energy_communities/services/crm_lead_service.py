import json
import logging

from odoo import _

from odoo.addons.component.core import Component

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

        # get user lang from payload
        lang = self._get_lang(params)

        # get utm source from payload
        target_source_xml_id = self._get_source_xml_id(params)

        if target_source_xml_id:
            # setup utm source on crm lead
            crm_lead_id = crm_lead.get("id", False)
            self._setup_lead_utm_source(crm_lead_id, target_source_xml_id)

            # select autoresponder notification id based on utm source
            template_external_id = self._get_autoresponder_email_template(
                target_source_xml_id
            )
            # add followers
            self.env["crm.lead"].browse(crm_lead_id).add_follower()

            # send auto responder email and notify admins
            email_values = {"email_to": params["email_from"], "lang": lang}

            if template_external_id:
                template = self.env.ref(
                    "energy_communities.{}".format(template_external_id)
                ).with_context(email_values)
                template.send_mail(force_send=True, res_id=crm_lead_id)
        return crm_lead

    def _setup_lead_utm_source(self, lead_id, source_xml_id):
        lead = self.env["crm.lead"].browse(lead_id)
        if lead:
            utm_source = self.env.ref("energy_communities." + source_xml_id)
            lead.write({"source_id": utm_source.id})

    def _get_source_xml_id(self, params):
        metadata = params["metadata"]
        target_source_xml_id = None
        for data in metadata:
            if data["key"] == "source_xml_id":
                target_source_xml_id = data["value"]
        return target_source_xml_id

    def _get_lang(self, params):
        metadata = params["metadata"]
        for data in metadata:
            if data["key"] == "current_lang":
                lang = data["value"]
        return lang

    def _get_autoresponder_email_template(self, source_xml_id):
        template_external_id = None
        if source_xml_id == "ce_source_creation_ce_proposal":
            template_external_id = "email_templ_lead_ce_creation_receipt_confirm_id"
        elif source_xml_id == "ce_source_existing_ce_contact":
            template_external_id = "email_templ_lead_request_contact_confirm_id"
        elif source_xml_id == "ce_source_existing_ce_info":
            template_external_id = "email_templ_lead_request_ce_news_confirm_id"
        elif source_xml_id == "ce_source_future_location_ce_info":
            template_external_id = (
                "email_templ_lead_request_advise_future_ce_confirm_id"
            )
        elif source_xml_id == "ce_source_general_info":
            template_external_id = "email_templ_lead_request_platform_news_confirm_id"
        return template_external_id
