import base64
from datetime import datetime

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .metadata_mapping_conf import (
    _LEAD_METADATA__DATE_FIELDS,
    _LEAD_METADATA__ENERGY_TAGS_FIELDS,
    _LEAD_METADATA__EXTID_FIELDS,
    _LEAD_METADATA__IMAGE_FIELDS,
    _LEAD_METADATA__LANG_FIELDS,
    _MAP__LEAD_METADATA__COMPANY_CREATION_WIZARD,
)


class CrmLead(models.Model):
    _name = "crm.lead"
    _inherit = ["crm.lead", "external.id.mixin", "user.currentcompany.mixin"]

    lang = fields.Char(string="Language")
    ce_tag_ids = fields.Many2many(
        "crm.tag",
        "crm_lead_ce_tag_rel",
        "lead_id",
        "tag_id",
        string="CE Tags",
        help="CE Classify and analyze categories",
    )
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
            team = self.env["crm.team"].get_create_default_sale_team(record.company_id)
            record.team_id = team.id

    def _get_default_community_wizard(self):
        self.ensure_one()
        # form values from metadata
        creation_dict = self._get_metadata_values()
        # all other populated form fields.
        creation_partner = self._search_partner_for_company_wizard_creation(
            creation_dict
        )
        if creation_partner:
            creation_dict["creation_partner"] = creation_partner.id
        users = [user.id for user in self.company_id.get_users()]
        users = users + [
            self.env.ref("base.user_admin").id,
            self.env.ref("base.public_user").id,
        ]
        creation_dict.update(
            {
                "parent_id": self.company_id.id,
                "crm_lead_id": self.id,
                "user_ids": users,
                "chart_template_id": self.env.ref(
                    "l10n_es.account_chart_template_pymes"
                ).id,
                "update_default_taxes": True,
                "default_sale_tax_id": self.env.ref(
                    "l10n_es.account_tax_template_s_iva21s"
                ).id,
                "default_purchase_tax_id": self.env.ref(
                    "l10n_es.account_tax_template_p_iva21_bc"
                ).id,
                "property_cooperator_account": self.env["account.account"]
                .search([("code", "like", "44000%")], limit=1)
                .id,
                "create_user": False,
                "create_landing": True,
            }
        )
        return creation_dict

    def _get_metadata_values(self):
        meta_dict = {}
        for meta_key in _MAP__LEAD_METADATA__COMPANY_CREATION_WIZARD.keys():
            meta_entry = self.metadata_line_ids.filtered(
                lambda meta: meta.key == meta_key
            )
            if meta_entry:
                wizard_key = _MAP__LEAD_METADATA__COMPANY_CREATION_WIZARD[meta_key]
                # date meta
                if meta_key in _LEAD_METADATA__DATE_FIELDS:
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
                # energy services
                elif meta_key in _LEAD_METADATA__ENERGY_TAGS_FIELDS:
                    energy_services = []
                    for energy_tag_xml_id in meta_entry.value.split(","):
                        try:
                            energy_tag = self.env.ref(
                                "energy_communities." + energy_tag_xml_id
                            )
                        except Exception:
                            energy_tag = False
                        if energy_tag:
                            energy_services.append(
                                (
                                    4,
                                    energy_tag.id,
                                )
                            )
                    meta_dict[wizard_key] = energy_services
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

    def get_metadata(self, meta_key):
        return self.metadata_line_ids.filtered(lambda record: record.key == meta_key)
