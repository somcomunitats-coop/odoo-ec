from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
                    lead._get_company_create_vals()
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

    def _get_company_create_vals(self):
        self.ensure_one()
        m_dict = {m.key: m.value for m in self.form_submission_metadata_ids}

        foundation_date = None
        if (
            m_dict.get("partner_foundation_date", False)
            and m_dict["partner_foundation_date"]
        ):
            date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"]
            for date_format in date_formats:
                try:
                    foundation_date = datetime.strptime(
                        m_dict["partner_foundation_date"], date_format
                    )
                except:
                    pass
            if not foundation_date:
                raise UserError(
                    _(
                        "The Foundation Date value {} have a non valid format. It must be: yyyy-mm-dd or dd-mm-yyyy or yyyy/mm/dd or dd/mm/yyyy"
                    ).format(m_dict["partner_foundation_date"])
                )

        initial_share_amount = 0.00
        if (
            m_dict.get("partner_initial_share_amount", False)
            and m_dict["partner_initial_share_amount"]
            or None
        ):
            try:
                initial_share_amount = float(m_dict["partner_initial_share_amount"])
            except:
                pass

        lang_id = None
        if m_dict.get("partner_language", False) and m_dict["partner_language"] or None:
            lang_id = self.env["res.lang"].search(
                [("code", "=", m_dict["partner_language"])], limit=1
            )

        create_vals = {
            "name": self.name,
            "street": self.street,
            "street2": self.street2,
            "city": self.city,
            "zip": self.zip,
            "state_id": self.state_id.id,
            "country_id": self.country_id.id,
            "website": self.website,
            "phone": self.phone,
            "email": self.email_from
            or (m_dict.get("contact_email", False) and m_dict["contact_email"])
            or None,
            "vat": m_dict.get("partner_vat", False) and m_dict["partner_vat"] or None,
            "social_twitter": m_dict.get("partner_twitter", False)
            and m_dict["partner_twitter"]
            or None,
            "social_facebook": m_dict.get("partner_facebook", False)
            and m_dict["partner_facebook"]
            or None,
            "social_instagram": m_dict.get("partner_instagram", False)
            and m_dict["partner_instagram"]
            or None,
            "social_telegram": m_dict.get("partner_telegram", False)
            and m_dict["partner_telegram"]
            or None,
            "create_user": True,
            "foundation_date": foundation_date,
            "initial_subscription_share_amount": initial_share_amount,
            "default_lang_id": lang_id and lang_id.id or None,
        }

        return create_vals

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


class CrmTags(models.Model):
    _inherit = "crm.tag"

    tag_ext_id = fields.Char("ID Ext tag", compute="compute_ext_id_tag")

    def compute_ext_id_tag(self):
        for record in self:
            res = record.get_external_id()
            record.tag_ext_id = False
            if res.get(record.id):
                record.tag_ext_id = res.get(record.id)
