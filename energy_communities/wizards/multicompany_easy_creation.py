import logging

from odoo import _, api, fields, models

from ..models.res_company import (
    _CE_MEMBER_STATUS_VALUES,
    _CE_STATUS_VALUES,
    _CE_TYPE,
    _HIERARCHY_LEVEL_BASE_VALUES,
    _LEGAL_FORM_VALUES,
)
from ..utils import get_successful_popup_message, user_role_utils

_logger = logging.getLogger(__name__)


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _name = "account.multicompany.easy.creation.wiz"
    _inherit = ["account.multicompany.easy.creation.wiz", "cm.coordinates.mixin"]

    parent_id = fields.Many2one(
        "res.company",
        string="Parent Coordinator Company",
        index=True,
        required=True,
        domain=[("hierarchy_level", "=", "coordinator")],
    )
    crm_lead_id = fields.Many2one("crm.lead", string="CRM Lead")
    chart_template_id = fields.Many2one(
        comodel_name="account.chart.template",
        string="Chart Template",
        domain=[("visible", "=", True)],
    )
    default_lang_id = fields.Many2one(
        comodel_name="res.lang",
        string="Language",
    )
    street = fields.Char(
        string="Address",
    )
    city = fields.Char(
        string="City",
    )
    zip_code = fields.Char(
        string="ZIP code",
    )
    foundation_date = fields.Date(string="Foundation date")
    vat = fields.Char(
        string="VAT",
    )
    email = fields.Char(
        string="Email",
    )
    phone = fields.Char(
        string="Phone",
    )
    website = fields.Char(
        string="Website",
    )
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State",
    )
    legal_form = fields.Selection(
        selection=_LEGAL_FORM_VALUES,
        string="Legal form",
    )
    legal_name = fields.Char(string="Legal name", required=True)
    ce_status = fields.Selection(
        selection=_CE_STATUS_VALUES,
        string="Energy Community state",
    )
    # Used in demo data, so it can finish the process before continuing with the rest of the demo data.
    hook_cron = fields.Boolean(
        default=True, string="Run the post hook in a cron job or not"
    )
    # overwrite users domain
    user_ids = fields.Many2many(
        comodel_name="res.users", string="Users allowed", domain=[]
    )
    # landing / public data
    create_landing = fields.Boolean(string="Create Landing", default=False)
    create_place = fields.Boolean(string="Create Map Place", default=False)
    landing_short_description = fields.Text(string="Short description")
    landing_long_description = fields.Text(string="Long description")
    energy_action_mids = fields.Many2many("energy.action", string="Energy Actions")
    ce_number_of_members = fields.Integer(string="Number of members")
    ce_member_status = fields.Selection(
        selection=_CE_MEMBER_STATUS_VALUES,
        default="open",
        string="Community status",
    )
    landing_why_become_cooperator = fields.Html(string="Why become cooperator")
    landing_become_cooperator_process = fields.Html(string="Become cooperator process")
    landing_primary_image_file = fields.Image("Primary Image")
    landing_secondary_image_file = fields.Image("Secondary Image")
    landing_logo_file = fields.Image("Logo Image")
    landing_community_type = fields.Selection(
        selection=_CE_TYPE,
        default="citizen",
        required=True,
        string="Community type",
    )
    ce_twitter_url = fields.Char(string="Twitter link")
    ce_telegram_url = fields.Char(string="Telegram link")
    ce_instagram_url = fields.Char(string="Instagram link")
    ce_facebook_url = fields.Char(string="Facebook link")
    # enable coordinator companies creation
    hierarchy_level = fields.Selection(
        selection=_HIERARCHY_LEVEL_BASE_VALUES,
        required=True,
        string="Hierarchy level",
        default="community",
    )
    creation_partner = fields.Many2one(
        "res.partner", string="Use existing partner linked to new company"
    )
    user_current_company = fields.Many2one(
        "res.company", compute="_compute_user_current_company", store=False
    )

    @api.depends("parent_id")
    def _compute_user_current_company(self):
        for record in self:
            record.user_current_company = self.env.user.user_current_company

    @api.onchange("hierarchy_level")
    def onchange_hierarchy_level(self):
        for record in self:
            if record.hierarchy_level == "community":
                if self.crm_lead_id:
                    company_id = self.crm_lead_id.company_id.id
                else:
                    company_id = False
                return {
                    "value": {"parent_id": company_id},
                    "domain": {"parent_id": [("hierarchy_level", "=", "coordinator")]},
                }
            if record.hierarchy_level == "coordinator":
                record.create_place = False
                return {
                    "value": {"parent_id": self.env.ref("base.main_company").id},
                    "domain": {"parent_id": [("hierarchy_level", "=", "instance")]},
                }

    def add_company_log(self):
        message = _(
            "Community created from: <a href='/web#id={id}&view_type=form&model=crm.lead&menu_id={menu_id}'>{name}</a>"
        )
        self_new_company = self.with_company(self.new_company_id)
        self_new_company.new_company_id.message_post(
            body=message.format(
                id=self.crm_lead_id.id,
                menu_id=self.env.ref("crm.crm_menu_root").id,
                name=self.crm_lead_id.name,
            )
        )

    def action_accept(self):
        self.create_company()
        self.apply_new_company_to_impacted_users()
        self.apply_new_company_partner_visibility()
        if self.create_landing:
            self.create_public_data()
        if self.crm_lead_id:
            self.add_company_log()
            self.crm_lead_id.action_set_won_rainbowman()
        if self.hook_cron:
            self.with_delay().thread_action_accept()
        else:
            self.thread_action_accept()

        return get_successful_popup_message(
            _("Company creation successful"),
            _("Community creation process has been started."),
        )

    def create_company(self):
        allow_new_members = False
        if self.ce_member_status == "open":
            allow_new_members = True
        vat = False
        if self.vat:
            vat = self.vat.replace(" ", "").upper()
        energy_action_ids = []
        for energy_action in self.energy_action_mids:
            energy_action_ids.append((0, 0, {"energy_action_id": energy_action.id}))
        self.new_company_id = (
            self.env["res.company"]
            .sudo()
            .create(
                {
                    "name": self.legal_name,
                    "hierarchy_level": self.hierarchy_level,
                    "user_ids": [(6, 0, self.user_ids.ids)],
                    "parent_id": self.parent_id.id,
                    "partner_id": self.creation_partner.id,
                    "street": self.street,
                    "website": self.website,
                    "email": self.email.strip(),
                    "foundation_date": self.foundation_date,
                    "vat": vat,
                    "city": self.city,
                    "state_id": self.state_id,
                    "zip": self.zip_code,
                    "legal_form": self.legal_form,
                    "comercial_name": self.name,
                    "ce_status": self.ce_status,
                    "phone": self.phone,
                    "default_lang_id": self.default_lang_id.id,
                    "allow_new_members": allow_new_members,
                    "social_twitter": self.ce_twitter_url,
                    "social_telegram": self.ce_telegram_url,
                    "social_instagram": self.ce_instagram_url,
                    "social_facebook": self.ce_facebook_url,
                    "logo": self.landing_logo_file,
                    "community_energy_action_ids": energy_action_ids,
                }
            )
        )

    def apply_new_company_to_impacted_users(self):
        system_impacted_user_id_list = [
            self.env.ref("base.public_user").id,
            self.env.ref("base.user_admin").id,
        ]
        # Apply new company to all users selected on wizard
        for user in self.user_ids:
            platform_admin_role = user.get_user_role_lines(
                role_codes=["role_platform_admin"]
            )
            # if user is a platform admin or system user: apply company_ids in order to gain visibility
            if platform_admin_role or user.id in system_impacted_user_id_list:
                user.write({"company_ids": [(4, self.new_company_id.id)]})
            else:
                new_company_hierarchy_level = self.new_company_id.hierarchy_level
                with user_role_utils(self.env, user) as component:
                    if new_company_hierarchy_level == "coordinator":
                        component.apply_coordinator_role_in_company(self.new_company_id)
                    if new_company_hierarchy_level == "community":
                        component.apply_coordinator_role_in_company(
                            self.new_company_id.parent_id
                        )

    def apply_new_company_partner_visibility(self):
        company_hierarchy_level = self.new_company_id.hierarchy_level
        if company_hierarchy_level == "coordinator":
            # apply to new company-partner all visible companies (company_ids)
            self.new_company_id.partner_id.write(
                {
                    "company_ids": [
                        (4, self.env.ref("base.main_company").id),
                        (4, self.new_company_id.id),
                    ]
                }
            )
        if company_hierarchy_level == "community":
            # apply to new company-partner all visible companies (company_ids)
            self.new_company_id.partner_id.write(
                {
                    "company_ids": [
                        (4, self.env.ref("base.main_company").id),
                        (4, self.parent_id.id),
                        (4, self.new_company_id.id),
                    ]
                }
            )
            # apply new company to coordinator-partner visible companies (company_ids)
            self.parent_id.partner_id.sudo().write(
                {
                    "company_ids": [
                        (4, self.new_company_id.id),
                    ]
                }
            )

    def create_public_data(self):
        new_landing = self.new_company_id.sudo().action_create_landing()
        new_landing.sudo().write(
            {
                "number_of_members": self.ce_number_of_members,
                "community_type": self.landing_community_type,
                "community_secondary_type": self.legal_form,
                "community_status": self.ce_member_status,
                "external_website_link": self.website,
                "primary_image_file": self.landing_primary_image_file,
                "secondary_image_file": self.landing_secondary_image_file,
                "short_description": self.landing_short_description,
                "long_description": self.landing_long_description,
                "why_become_cooperator": self.landing_why_become_cooperator,
                "become_cooperator_process": self.landing_become_cooperator_process,
                "lat": self.lat,
                "lng": self.lng,
                "street": self.street,
                "postal_code": self.zip_code,
                "city": self.city,
            }
        )
        if self.create_place:
            new_landing.sudo().create_landing_place()

    def thread_action_accept(self):
        self.configure_community_accounting()
        self.update_taxes()
        self.update_properties()

    def configure_community_accounting(self):
        allowed_company_ids = (
            self.env.context.get("allowed_company_ids", []) + self.new_company_id.ids
        )
        new_company = self.new_company_id.with_context(
            allowed_company_ids=allowed_company_ids
        )
        self.with_context(
            allowed_company_ids=allowed_company_ids
        ).sudo().chart_template_id.try_loading(company=new_company)
        self.create_bank_journals()
        self.create_sequences()
