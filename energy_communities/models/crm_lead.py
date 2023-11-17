from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_TAG_TYPE_VALUES = [
    ("regular", _("Regular")),
    ("energy_service", _("Energy Service")),
    ("service_plan", _("Service Plan")),
]


class CrmLead(models.Model):
    _inherit = "crm.lead"

    lang = fields.Char(string="Language")
    ce_tag_ids = fields.Many2many(
        "crm.tag",
        "crm_lead_ce_tag_rel",
        "lead_id",
        "tag_id",
        string="CE Tags",
        help="CE Classify and analyze categories",
    )
    community_company_id = fields.Many2one(
        string="Related Community",
        comodel_name="res.company",
        domain="[('coordinator','!=',True)]",
        help="Community related to this Lead",
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
    is_instance_company = fields.Boolean(
        string="Is instance company", compute="_is_instance_company"
    )

    def _is_instance_company(self):
        company = self.env.company
        instance_companies = self.env["res.company"].search(
            [("hierarchy_level", "=", "instance")]
        )
        if company in instance_companies:
            self.is_instance_company = True
        else:
            self.is_instance_company = False

    def _build_community_company(self):
        if not self.env.user.company_id.coordinator:
            raise UserError(
                _(
                    "Only users that belongs to the 'Coordinator' company can create new Companies from Leads."
                )
            )

        creation_ce_source_id = self.env["ir.model.data"].get_object_reference(
            "ce", "ce_source_creation_ce_proposal"
        )[1]

        # build company for each Lead
        for lead in self:
            if not lead.source_id or lead.source_id.id != creation_ce_source_id:
                raise UserError(
                    _(
                        "The Source {} of Lead {} do not allow the creation of new Companies"
                    ).format(lead.source_id.name, lead.name)
                )

            if not lead.community_company_id:
                # Create the new company using very basic starting Data
                company = self.env["res.company"].create(
                    lead._get_default_community_wizard()
                )

                # Update Lead & Map Place (if exist) fields accordingly
                lead.community_company_id = company.id
                if lead.team_id and lead.team_type == "map_place_proposal":
                    lead.team_id.community_company_id = company.id

        # we need to do this commit before proceed to call KeyCloak API calls to build the related KC realms
        # TODO Check if this commit is needed, commented to comply the pre-commit
        # self._cr.commit()

        # build keyKloac realm for each new existing new company
        for lead in self:
            if lead.community_company_id:
                lead.community_company_id._create_keycloak_realm()
                lead.community_company_id._community_post_keycloak_creation_tasks()

    def _get_default_community_wizard(self):
        self.ensure_one()
        metadata = {m.key: m.value for m in self.metadata_line_ids}

        foundation_date = None
        if metadata.get("ce_creation_date", False) and metadata["ce_creation_date"]:
            date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"]
            for date_format in date_formats:
                try:
                    foundation_date = datetime.strptime(
                        metadata["ce_creation_date"], date_format
                    )
                except:
                    pass
            if not foundation_date:
                raise UserError(
                    _(
                        "The Foundation Date value {} have a non valid format. It must be: yyyy-mm-dd or dd-mm-yyyy or yyyy/mm/dd or dd/mm/yyyy"
                    ).format(metadata["partner_foundation_date"])
                )

        lang_id = None
        if metadata.get("current_lang", False) and metadata["current_lang"] or None:
            lang_id = self.env["res.lang"].search(
                [("code", "=", metadata["current_lang"])], limit=1
            )

        users = [user.id for user in self.company_id.get_users()]

        return {
            "name": self.name,
            "parent_id": self.company_id.id,
            "crm_lead_id": self.id,
            "user_ids": users,
            "street": metadata.get("ce_address", False)
            and metadata["ce_address"]
            or None,
            "city": metadata.get("ce_city", False) and metadata["ce_city"] or None,
            "zip_code": metadata.get("ce_zip", False) and metadata["ce_zip"] or None,
            "phone": metadata.get("contact_phone", False)
            and metadata["contact_phone"]
            or None,
            "email": metadata.get("email_from", False)
            and metadata["email_from"]
            or None,
            "vat": metadata.get("ce_vat", False) and metadata["ce_vat"] or None,
            "foundation_date": foundation_date,
            "default_lang_id": lang_id and lang_id.id or None,
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
        }

    def _create_keycloak_realm(self):
        for lead in self:
            if not lead.community_company_id:
                raise UserError(
                    _(
                        "Unable to create the KeyCloack entities from Lead: {}, because it is not yet related to any Community company"
                    ).format(lead.name)
                )
            lead.community_company_id._create_keycloak_realm()

    def _create_community_initial_users(self):
        for lead in self:
            pass

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


class CrmTags(models.Model):
    _inherit = "crm.tag"

    tag_ext_id = fields.Char("ID Ext tag", compute="compute_ext_id_tag")
    tag_type = fields.Selection(_TAG_TYPE_VALUES, string="Tag type", default="regular")

    def compute_ext_id_tag(self):
        for record in self:
            res = record.get_external_id()
            record.tag_ext_id = False
            if res.get(record.id):
                record.tag_ext_id = res.get(record.id)
