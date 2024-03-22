import ast
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

        # get utm source from payload
        target_source_xml_id = self._get_metadata_value(params, "source_xml_id")

        if target_source_xml_id:
            crm_lead_id = crm_lead.get("id", False)
            # setup lead name and description
            self._set_name(crm_lead_id, params)
            self._set_description(crm_lead_id, params)
            # setup utm source on crm lead
            utm_source = self._setup_lead_utm_source(crm_lead_id, target_source_xml_id)
            # map lead fields based on configuration
            self._map_metadata_crm_fields(crm_lead_id, utm_source, params)
            # email autoresponder
            self._lead_creation_email_autoresponder(
                crm_lead_id, target_source_xml_id, params
            )

        return crm_lead

    def _setup_lead_utm_source(self, lead_id, source_xml_id):
        lead = self.env["crm.lead"].browse(lead_id)
        if lead:
            utm_source = self.env.ref("energy_communities." + source_xml_id)
            lead.write({"source_id": utm_source.id})
            return utm_source
        return False

    def _map_metadata_crm_fields(self, crm_lead_id, utm_source, params):
        rel_mapping = utm_source.crm_lead_metadata_mapping_id
        if rel_mapping:
            crm_update_dict = {}
            for mapping_field in rel_mapping.metadata_mapping_field_ids:
                if mapping_field.type == "value_field":
                    crm_update_dict[
                        mapping_field.destination_field_key
                    ] = self._get_metadata_value(params, mapping_field.metadata_key)
                if mapping_field.type == "many2one_relation_field":
                    mapping_domain_initial = mapping_field.parse_mapping_domain()
                    mapping_domain = []
                    for domain_item in mapping_domain_initial:
                        if type(domain_item) is list:
                            # if the condition is a dict then construct a new domain based on the metadata value
                            try:
                                domain_item_value = ast.literal_eval(domain_item[2])
                                mapping_domain.append(
                                    [
                                        domain_item[0],
                                        domain_item[1],
                                        self._get_metadata_value(
                                            params, domain_item_value["metadata"]
                                        ),
                                    ]
                                )
                            # normal domain
                            except:
                                mapping_domain.append(domain_item)
                        else:
                            mapping_domain.append(domain_item)
                    res_ids = self.env[mapping_field.mapping_model_real].search(
                        mapping_domain
                    )
                    if res_ids:
                        crm_update_dict[mapping_field.destination_field_key] = res_ids[
                            0
                        ].id
            if crm_update_dict:
                self.env["crm.lead"].browse(crm_lead_id).write(crm_update_dict)
                return True
        return False

    def _lead_creation_email_autoresponder(
        self, crm_lead_id, target_source_xml_id, params
    ):
        # get user lang from payload
        lang = self._get_metadata_value(params, "current_lang")
        # select autoresponder notification id based on utm source
        template_external_id = self._get_autoresponder_email_template(
            target_source_xml_id
        )
        # add followers
        self.env["crm.lead"].browse(crm_lead_id).add_follower()
        # send auto responder email and notify admins
        email_values = {"email_to": params["email_from"]}
        if lang:
            email_values["lang"] = lang
        if template_external_id:
            template = self.env.ref(
                "energy_communities.{}".format(template_external_id)
            ).with_context(email_values)
            template.send_mail(force_send=False, res_id=crm_lead_id)
            return True
        return False

    def _get_metadata_value(self, params, key):
        metadata = params["metadata"]
        value = ""
        for data in metadata:
            if data["key"] == key:
                value = data["value"]
        return value

    def _set_name(self, lead_id, params):
        source_xml_id = self._get_metadata_value(params, "source_xml_id")
        lead = self.env["crm.lead"].browse(lead_id)
        email = params["email_from"]
        prefix = ""
        if source_xml_id == "ce_source_existing_ce_contact":
            prefix = _("[Contact CE]")
        elif source_xml_id == "ce_source_existing_ce_info":
            prefix = _("[Newsletter CE]")
        elif source_xml_id == "ce_source_general_contact":
            prefix = _("[Contact SomComunitats]")
        elif source_xml_id == "ce_source_general_info":
            prefix = _("[Newsletter SomComunitats]")
        elif source_xml_id == "ce_source_coord_web_hiring":
            prefix = _("[Hire Coord]")
        elif source_xml_id == "ce_source_coord_web_other":
            prefix = _("[Other Coord]")
        if source_xml_id == "ce_source_creation_ce_proposal":
            prefix = _("[Subscription CE]")
            ce_name = self._get_metadata_value(params, "ce_name")
            name = "{prefix} {lead_id} {ce_name}".format(
                prefix=prefix, lead_id=lead_id, ce_name=ce_name
            )
        else:
            name = "{prefix} {lead_id} {email}".format(
                prefix=prefix, lead_id=lead_id, email=email
            )
        if lead:
            lead.write({"name": name})

    def _set_description(self, lead_id, params):
        source_xml_id = self._get_metadata_value(params, "source_xml_id")
        lead = self.env["crm.lead"].browse(lead_id)
        description = ""
        if source_xml_id == "ce_source_creation_ce_proposal":
            ce_description = self._get_metadata_value(params, "ce_description")
            comments = self._get_metadata_value(params, "comments")
            description = "{ce_description} {comments}".format(
                ce_description=ce_description, comments=comments
            )
        if (
            source_xml_id == "ce_source_existing_ce_contact"
            or source_xml_id == "ce_source_general_contact"
        ):
            contact_motive = self._get_metadata_value(params, "contact_motive")
            message = self._get_metadata_value(params, "message")
            description = "{contact_motive}: {message}".format(
                contact_motive=contact_motive, message=message
            )
        if lead:
            lead.write({"description": description})

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
        elif source_xml_id == "ce_source_general_contact":
            template_external_id = "email_templ_contact_platform_confirm_id"
        elif source_xml_id == "ce_source_coord_web_hiring":
            template_external_id = "email_templ_lead_ce_source_coord_web_hiring_id"
        elif source_xml_id == "ce_source_coord_web_other":
            template_external_id = "email_templ_lead_ce_source_coord_web_other_id"
        return template_external_id
