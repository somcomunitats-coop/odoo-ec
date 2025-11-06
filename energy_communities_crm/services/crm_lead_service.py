import ast
import json
import logging
import re

from odoo import _

from odoo.addons.component.core import Component

# from odoo.addons.base_rest import restapi

_logger = logging.getLogger(__name__)


class CRMLeadService(Component):
    _inherit = "crm.lead.service"
    _name = "crm.lead.service"
    _description = """
        CRMLead requests
    """
    _collection = "crm.api.services"
    _usage = "crm-lead"

    DISCARD_EC_NAMES_RE = re.compile(r"\[(ON-HOLD|TO-DELETE)\]?i")

    def create(self, **params):
        # check if coordinator found
        added_coordinator = self._add_coordinator_to_metadata(params)
        crm_lead_create_respose = super().create(params)
        target_source_xml_id = self._get_metadata_value(params, "source_xml_id")
        if target_source_xml_id:
            crm_lead_dict = json.loads(
                crm_lead_create_respose.response[0].decode("utf-8")
            )
            crm_lead = self.env["crm.lead"].browse(crm_lead_dict.get("id", False))

            # if coordinator not found, post a message
            if not added_coordinator and self._get_coordinator_know_value(params):
                metadata = self._convert_params_metadata_to_dict(params)
                crm_lead.message_post(
                    body=f"""The coordinating entity corresponding to the metadata value
                    coordinator_landing_id = {metadata.get("coordinator_landing_id")}
                    and coordinator name {metadata.get("coordinator_name")} could not be identified."""
                )

            # update some fields based on the selected xml source
            utm_source = self.env.ref("energy_communities." + target_source_xml_id)
            lead_update_dict = {
                "name": self._get_crm_lead_name(crm_lead.id, params),
                "description": self._get_crm_lead_description(params),
                "source_id": utm_source.id,
            }
            # update only team_id an stage_id if it's overwriten by source
            team_and_stage_from_source = (
                self._get_team_and_stage_update_dict_from_source(utm_source)
            )
            if team_and_stage_from_source:
                lead_update_dict = lead_update_dict | team_and_stage_from_source
            lead_update_dict.update(self._map_metadata_crm_fields(utm_source, params))
            crm_lead.write(lead_update_dict)
            # email autoresponder
            self._lead_creation_email_autoresponder(
                crm_lead.id, target_source_xml_id, params
            )
        return crm_lead_create_respose

    def _get_company_in_coordinator_landing(self, coordinator_landing_id):
        try:
            coordinator_landing_id = int(coordinator_landing_id)
        except ValueError:
            _logger.error(
                f"Error: coordinator_landing_id is not an integer: {coordinator_landing_id}"
            )
            return False
        else:
            coordinator_landing = self.env["landing.page"].search(
                [("wp_landing_page_id", "=", coordinator_landing_id)]
            )
            return coordinator_landing.company_id if coordinator_landing else False

    def _get_coordinator_know_value(self, params):
        for metadata_line in params.get("metadata", []):
            if metadata_line.get("key") == "known_coordinator":
                return metadata_line.get("value") == "yes"
        return False

    def _add_coordinator_to_metadata(self, params):
        if not self._get_coordinator_know_value(params):
            return False
        coordinator_landing_id = self._get_metadata_value(
            params, "coordinator_landing_id"
        )
        if not coordinator_landing_id:
            return False
        company = self._get_company_in_coordinator_landing(coordinator_landing_id)
        if not company:
            return False
        can_append_coordinator = all(
            [
                company,
                company.hierarchy_level == "coordinator",
                not self.DISCARD_EC_NAMES_RE.fullmatch(company.name),
            ]
        )
        if not can_append_coordinator:
            return False
        params["metadata"].append({"key": "coordinator_id", "value": company.id})
        return True

    # TODO: Add contact coordinator source mapping
    def _get_crm_lead_name(self, lead_id, params):
        source_xml_id = self._get_metadata_value(params, "source_xml_id")
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
        elif source_xml_id == "ce_source_tariffs_page_contact":
            prefix = _("[Tariffs contact]")
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
        return name

    def _get_crm_lead_description(self, params):
        source_xml_id = self._get_metadata_value(params, "source_xml_id")
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
        return description

    def _get_team_and_stage_update_dict_from_source(self, utm_source):
        utm_team_id_id = self._get_team_id_from_source(utm_source)
        utm_stage_id_id = self._get_stage_id_from_team_id(utm_team_id_id)
        if utm_team_id_id and utm_stage_id_id:
            return {
                "team_id": utm_team_id_id,
                "stage_id": utm_stage_id_id,
            }
        return False

    def _get_team_id_from_source(self, utm_source):
        if utm_source.crm_team_id:
            return utm_source.crm_team_id.id
        return False

    def _get_stage_id_from_team_id(self, team_id_id=False):
        # perform search, return the first found
        stage_id = self.env["crm.stage"].search(
            [("team_id", "=", team_id_id)], order="sequence, id", limit=1
        )
        if stage_id:
            return stage_id.id
        return False

    def _map_metadata_crm_fields(self, utm_source, params):
        crm_update_dict = {}
        rel_mapping = utm_source.crm_lead_metadata_mapping_id
        if rel_mapping:
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
        return crm_update_dict

    def _get_metadata_value(self, params, key):
        metadata_dict = self._convert_params_metadata_to_dict(params)
        return metadata_dict.get(key, False)

    def _convert_params_metadata_to_dict(self, params):
        metadata_dict = {}
        for metadata_item in params.get("metadata", []):
            metadata_dict[metadata_item["key"]] = metadata_item["value"]
        return metadata_dict

    def _lead_creation_email_autoresponder(
        self, crm_lead_id, target_source_xml_id, params
    ):
        # add followers
        self.env["crm.lead"].browse(crm_lead_id).add_follower()
        # select autoresponder notification id based on utm source
        template_external_id = self._get_autoresponder_email_template(
            target_source_xml_id
        )
        if template_external_id:
            # setup context data to be used on template
            email_values = {
                "metadata": self._convert_params_metadata_to_dict(params),
                "email_to": params["email_from"],
            }
            template = self.env.ref(
                "energy_communities_crm.{}".format(template_external_id)
            ).with_context(email_values)
            template.send_mail(
                force_send=True,
                res_id=crm_lead_id,
                email_layout_xmlid="mail.mail_notification_layout",
            )
            return True
        return False

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
        elif source_xml_id == "ce_source_tariffs_page_contact":
            template_external_id = "email_templ_lead_ce_source_tariffs_page_contact"

        return template_external_id
