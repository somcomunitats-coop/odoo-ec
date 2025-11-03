import base64
import logging
from datetime import datetime

import requests
from stdnum.es import iban

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.energy_communities.config import (
    CHART_OF_ACCOUNTS_GENERAL_CANARY_REF,
    CHART_OF_ACCOUNTS_GENERAL_REF,
    CHART_OF_ACCOUNTS_NON_PROFIT_CANARY_REF,
    CHART_OF_ACCOUNTS_NON_PROFIT_REF,
    STATE_CANARY_GC,
    STATE_CANARY_TF,
)
from odoo.addons.energy_communities.models.res_company import (
    _LEGAL_FORM_VALUES_DEFAULT,
    _LEGAL_FORM_VALUES_NON_PROFIT,
)

from ..config import (
    _LEAD_METADATA__DATE_FIELDS,
    _LEAD_METADATA__ENERGY_TAGS_FIELDS,
    _LEAD_METADATA__EXTID_FIELDS,
    _LEAD_METADATA__IMAGE_FIELDS,
    _LEAD_METADATA__LANG_FIELDS,
    _MAP__LEAD_METADATA__COMPANY_CREATION_WIZARD,
    COMPANY_CREATION_WIZARD_DEFAULT_TAXES,
)

logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _name = "crm.lead"
    _inherit = ["crm.lead", "external.id.mixin", "user.currentcompany.mixin"]

    lang = fields.Char(string="Language")
    finished = fields.Boolean(
        related="stage_id.is_won",
        readonly=True,
    )
    company_hierarchy_level = fields.Selection(
        related="company_id.hierarchy_level",
        readonly=True,
    )
    can_be_assigned_to_coordinator = fields.Boolean(
        string="Can be assigned to coordinator",
        compute="_get_can_be_assigned_to_coordinator",
        store=False,
    )
    ce_child_lead_id = fields.Many2one(comodel_name="crm.lead", string="Crm lead child")

    @api.constrains("company_id")
    def validate_lead_conf(self):
        for record in self:
            if record.team_id.company_id.id != record.company_id.id:
                raise ValidationError(
                    _(
                        "Crm Lead team {team_name} doesn't match it's company {company_name}"
                    ).format(
                        **{
                            "team_name": record.team_id.name,
                            "company_name": record.company_id.name,
                        }
                    )
                )
            if record.stage_id.team_id.id != record.team_id.id:
                raise ValidationError(
                    _(
                        "Crm Lead stage {stage_name} doesn't match it's company {company_name}"
                    ).format(
                        **{
                            "stage_name": record.stage_id.name,
                            "company_name": record.company_id.name,
                        }
                    )
                )

    @api.onchange("company_id")
    def _auto_setup_team_id_domain(self):
        for record in self:
            return {
                "domain": {"team_id": [("company_id", "=", record.company_id.id)]},
            }

    @api.depends("company_id")
    def _compute_team_id(self):
        for record in self:
            if (
                not record.team_id
                or record.team_id.company_id.id != record.company_id.id
            ):
                team = self.env["crm.team"].get_create_default_sale_team(
                    record.company_id
                )
                record.team_id = team.id

    def _get_default_community_wizard(self):
        self.ensure_one()
        # form values from metadata
        creation_dict = self._get_metadata_values()
        # Check metadata coordinator_id with context company_id
        if creation_dict.get("coordinator_id", False):
            coordinator = self.env["res.company"].browse(
                int(creation_dict["coordinator_id"])
            )
            if (
                coordinator
                and coordinator.hierarchy_level == "coordinator"
                and coordinator.id != self.env.company.id
            ):
                raise ValidationError(
                    _(
                        f"""
                    The lead metadata with key coordinator_id
                    ({creation_dict.get("coordinator_id", False)}: {creation_dict.get("coordinator_name", False)})
                    points to a coordinator other than the active one in the user's context
                    ({self.env.company.id}: {self.env.company.name}).
                    """
                    )
                )
        if creation_dict.get("coordinator_id", False):
            del creation_dict["coordinator_id"]
        if creation_dict.get("coordinator_name", False):
            del creation_dict["coordinator_name"]
        # all other populated form fields.
        creation_partner = self._search_partner_for_company_wizard_creation(
            creation_dict
        )
        creation_dict.update(
            {
                "parent_id": self.company_id.id,
                "crm_lead_id": self.id,
                "user_ids": self.env[
                    "account.multicompany.easy.creation.wiz"
                ]._get_company_creation_related_users_list(self.company_id),
                "chart_template_id": self._get_chart_template_id_from_meta(),
                "update_default_taxes": True,
                "default_sale_tax_id": self.env.ref(
                    COMPANY_CREATION_WIZARD_DEFAULT_TAXES[
                        "canary" if self._is_canary_state() else "general"
                    ]["default_sale_tax_id"]
                ).id,
                "default_purchase_tax_id": self.env.ref(
                    COMPANY_CREATION_WIZARD_DEFAULT_TAXES[
                        "canary" if self._is_canary_state() else "general"
                    ]["default_purchase_tax_id"]
                ).id,
                "create_user": False,
                "create_landing": True,
                "create_place": True,
                "creation_partner": creation_partner.id if creation_partner else False,
                "default_lang_id": self.lang_id.id,
            }
        )

        if creation_dict.get("legal_form", "other") == "other":
            creation_dict.update({"legal_form": _LEGAL_FORM_VALUES_DEFAULT})

        ce_iban_1 = creation_dict.get("ce_iban_1", False)
        if ce_iban_1:
            try:
                iban.validate(ce_iban_1)
                creation_dict.update({"bank_ids": [(0, 0, {"acc_number": ce_iban_1})]})
            except Exception as e:
                logger.warning(
                    _(
                        f"""
                    The lead metadata with key ce_iban_1
                    ({ce_iban_1}) is invalid: {e}
                    """
                    )
                )
        if creation_dict.get("ce_iban_1", False):
            del creation_dict["ce_iban_1"]

        if creation_dict.get("legal_form", "other") == "non_profit":
            if creation_dict.get("ce_member_recurrent_contribution_date", False):
                creation_dict.update(
                    {
                        "fixed_invoicing_day": creation_dict.get(
                            "ce_member_recurrent_contribution_date"
                        ).strftime("%d"),
                        "fixed_invoicing_month": creation_dict.get(
                            "ce_member_recurrent_contribution_date"
                        ).strftime("%m"),
                    }
                )
        if creation_dict.get("ce_member_recurrent_contribution_date", False):
            del creation_dict["ce_member_recurrent_contribution_date"]

        return creation_dict

    def _get_chart_template_id_from_meta(self):
        meta_entry = self.metadata_line_ids.filtered(
            lambda meta: meta.key == "ce_legal_form"
        )
        if self._is_canary_state() and meta_entry:
            if meta_entry.value in _LEGAL_FORM_VALUES_NON_PROFIT:
                return self.env.ref(CHART_OF_ACCOUNTS_NON_PROFIT_CANARY_REF).id
            return self.env.ref(CHART_OF_ACCOUNTS_GENERAL_CANARY_REF).id
        if meta_entry:
            if meta_entry.value in _LEGAL_FORM_VALUES_NON_PROFIT:
                return self.env.ref(CHART_OF_ACCOUNTS_NON_PROFIT_REF).id
        return self.env.ref(CHART_OF_ACCOUNTS_GENERAL_REF).id

    def _is_canary_state(self):
        state = self.metadata_line_ids.filtered(lambda meta: meta.key == "ce_state")
        if state:
            if int(state.value) in [
                self.env.ref(STATE_CANARY_TF).id,
                self.env.ref(STATE_CANARY_GC).id,
            ]:
                return True
        return False

    def _get_metadata_values(self):
        meta_dict = {}
        for meta_key in _MAP__LEAD_METADATA__COMPANY_CREATION_WIZARD.keys():
            meta_entry = self.metadata_line_ids.filtered(
                lambda meta: meta.key == meta_key
            )
            if meta_entry:
                wizard_key = _MAP__LEAD_METADATA__COMPANY_CREATION_WIZARD[meta_key]
                # ce_status meta
                if meta_key == "ce_constitution_status":
                    if meta_entry.value == "constituted":
                        meta_dict[wizard_key] = "active"
                    else:
                        meta_dict[wizard_key] = "building"
                # date meta
                elif meta_key in _LEAD_METADATA__DATE_FIELDS:
                    format_date = self._format_date_for_company_wizard_creation(
                        meta_entry.value
                    )
                    if format_date:
                        meta_dict[wizard_key] = format_date
                # lang meta
                elif meta_key in _LEAD_METADATA__LANG_FIELDS:
                    lang_id = self.env["res.lang"].search(
                        [("code", "=", meta_entry.value)], limit=1
                    )
                    if lang_id:
                        meta_dict[wizard_key] = lang_id.id
                # energy actions
                elif meta_key in _LEAD_METADATA__ENERGY_TAGS_FIELDS:
                    energy_actions = []
                    for energy_action_xml_id in meta_entry.value.split(","):
                        try:
                            energy_action = self.env.ref(
                                "energy_communities.{}".format(energy_action_xml_id)
                            )
                        except Exception:
                            energy_action = False
                        if energy_action:
                            energy_actions.append(
                                (
                                    4,
                                    energy_action.id,
                                )
                            )
                    meta_dict[wizard_key] = energy_actions
                # images
                elif meta_key in _LEAD_METADATA__IMAGE_FIELDS:
                    img_url = "{base_url}/web/image/{attachment_id}".format(
                        base_url=self.env["ir.config_parameter"].get_param(
                            "web.base.url"
                        ),
                        attachment_id=meta_entry.value,
                    )
                    # attachment = self.env['ir.attachment'].search([('id','=',meta_entry.value)])
                    # attachment_path = attachment._full_path(attachment.store_fname)
                    # with open(attachment_path, 'rb') as img:
                    #     meta_dict[wizard_key] = base64.b64encode(img.read())
                    response = requests.get(img_url)
                    if response.ok and response.content:
                        meta_dict[wizard_key] = base64.b64encode(response.content)
                # all other fields
                else:
                    # control external ids numeric
                    if meta_key in _LEAD_METADATA__EXTID_FIELDS:
                        if meta_entry.value.isdigit():
                            meta_dict[wizard_key] = meta_entry.value
                    else:
                        meta_dict[wizard_key] = meta_entry.value
                if "name" not in meta_dict.keys():
                    raise UserError(
                        _("Metadata 'ce_name' must be defined for creating a company")
                    )
                if "legal_name" not in meta_dict.keys():
                    meta_dict["legal_name"] = meta_dict["name"]
                if "vat" in meta_dict.keys():
                    meta_dict["vat"] = meta_dict["vat"].replace(" ", "").upper()
                if "email" in meta_dict.keys():
                    meta_dict["email"] = meta_dict["email"].strip()
        return meta_dict

    def _search_partner_for_company_wizard_creation(self, creation_dict):
        creation_partner = False
        if "vat" in creation_dict.keys():
            creation_partners = self.env["res.partner"].search(
                [
                    ("company_ids", "in", self.env.user.get_current_company_id()),
                    ("vat", "=", creation_dict["vat"]),
                ]
            )
            if creation_partners:
                creation_partner = creation_partners[0]
                # more than one partner found -> filter by email
                if len(creation_partners) > 1 and "email" in creation_dict.keys():
                    email_creation_partners = creation_partners.filtered(
                        lambda record: record.email == creation_dict["email"]
                    )
                    if email_creation_partners:
                        creation_partner = email_creation_partners[0]
        return creation_partner

    def _format_date_for_company_wizard_creation(self, date_val):
        format_date = False
        date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"]
        for date_format in date_formats:
            try:
                format_date = datetime.strptime(date_val, date_format)
            except:
                pass
        return format_date

    def action_assign_crm_to_coordinator_company(self):
        return {
            "name": _("Assign CRM to coordinator company"),
            "type": "ir.actions.act_window",
            "res_model": "assign.crm.to.coordinator.company.wizard",
            "view_mode": "form",
            "target": "new",
        }

    def action_create_community(self):
        data = self._get_default_community_wizard()
        wizard = self.env["account.multicompany.easy.creation.wiz"].create(data)
        return {
            "type": "ir.actions.act_window",
            "name": _("Create community"),
            "res_model": "account.multicompany.easy.creation.wiz",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }

    @api.depends("source_id")
    def _get_can_be_assigned_to_coordinator(self):
        for record in self:
            record.can_be_assigned_to_coordinator = (
                record.source_id.id
                in [
                    self.env.ref("energy_communities.ce_source_general_info").id,
                    self.env.ref("energy_communities.ce_source_existing_ce_contact").id,
                    self.env.ref(
                        "energy_communities.ce_source_creation_ce_proposal"
                    ).id,
                ]
                and self.company_id.hierarchy_level == "instance"
            )

    def add_follower(self):
        instance_admin = self.env.ref("energy_communities.role_ce_manager").id
        company_id = self.company_id.id
        followers = self.env["res.users"].search(
            [
                ("role_line_ids.role_id", "=", instance_admin),
                ("company_ids.id", "=", company_id),
            ]
        )
        if followers:
            self.message_subscribe(partner_ids=followers.partner_id.ids)

    def create_update_metadata(self, meta_key, meta_value):
        existing_meta = self.metadata_line_ids.filtered(
            lambda record: record.key == meta_key
        )
        if existing_meta:
            if existing_meta.value != meta_value:
                existing_meta.write({"value": meta_value})
                return True
        else:
            self.env["crm.lead.metadata.line"].create(
                {"key": meta_key, "value": meta_value, "crm_lead_id": self.id}
            )
            return True
        return False

    def delete_metadata(self, meta_key):
        existing_meta = self.metadata_line_ids.filtered(
            lambda record: record.key == meta_key
        )
        if existing_meta:
            existing_meta.unlink()
            return True
        return False

    def get_metadata_line(self, meta_key):
        return self.metadata_line_ids.filtered(lambda record: record.key == meta_key)
