import logging

from odoo import _, api, fields, models

from ..models.res_company import (
    _CE_MEMBER_STATUS_VALUES,
    _CE_STATUS_VALUES,
    _CE_TYPE,
    _HIERARCHY_LEVEL_BASE_VALUES,
    _LEGAL_FORM_VALUES,
)

_logger = logging.getLogger(__name__)


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _name = "account.multicompany.easy.creation.wiz"
    _inherit = ["account.multicompany.easy.creation.wiz", "cm.coordinates.mixin"]

    def _default_product_share_template(self):
        return self.env.ref(
            "energy_communities.share_capital_product_template",
            raise_if_not_found=False,
        )

    parent_id = fields.Many2one(
        "res.company",
        string="Parent Coordinator Company",
        index=True,
        required=True,
        domain=[("hierarchy_level", "=", "coordinator")],
    )
    crm_lead_id = fields.Many2one("crm.lead", string="CRM Lead")
    property_cooperator_account = fields.Many2one(
        comodel_name="account.account",
        string="Cooperator Account",
        help="This account will be"
        " the default one as the"
        " receivable account for the"
        " cooperators",
    )
    capital_share = fields.Monetary(string="Initial capital share", default=100)
    create_user = fields.Boolean(string="Create user for cooperator", default=True)
    chart_template_id = fields.Many2one(
        comodel_name="account.chart.template",
        string="Chart Template",
        domain=[("visible", "=", True)],
    )
    product_share_template = fields.Many2one(
        comodel_name="product.template",
        default=_default_product_share_template,
        string="Product Share Template",
        domain=[("is_share", "=", True)],
    )
    new_product_share_template = fields.Many2one(
        comodel_name="product.template",
        string="New Product Share Template",
        readonly=True,
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
    landing_short_description = fields.Text(string="Short description")
    landing_long_description = fields.Text(string="Long description")
    ce_tag_ids = fields.Many2many("crm.tag", string="Energy Community Services")
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
                return {
                    "value": {"parent_id": self.env.ref("base.main_company").id},
                    "domain": {"parent_id": [("hierarchy_level", "=", "instance")]},
                }

    def add_company_managers(self):
        coord_members = self.parent_id.get_users(
            ["role_coord_admin", "role_coord_worker"]
        )
        for manager in coord_members:
            manager.make_ce_user(self.new_company_id.id, "role_ce_manager")

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

    def create_default_utm_stage(self):
        self.env["utm.stage"].sudo().create(
            {"name": _("New"), "company_id": self.new_company_id.id}
        )

    def update_product_category_company_share(self):
        new_company_id = self.new_company_id.id
        self_new_company = self.with_company(new_company_id)
        product_category_company_share = self_new_company.env.ref(
            "cooperator.product_category_company_share"
        )
        account_chart_external_id = list(
            self.chart_template_id.get_external_id().values()
        )[0]
        values = {
            "l10n_es.account_chart_template_pymes": {
                "property_account_income_categ_id": "l10n_es.{}_account_pymes_100".format(
                    new_company_id
                ),
                "property_account_expense_categ_id": "l10n_es.{}_account_pymes_100".format(
                    new_company_id
                ),
            },
            "l10n_es.account_chart_template_assoc": {
                "property_account_income_categ_id": "l10n_es.{}_account_assoc_100".format(
                    new_company_id
                ),
                "property_account_expense_categ_id": "l10n_es.{}_account_assoc_100".format(
                    new_company_id
                ),
            },
            "l10n_es.account_chart_template_full": {
                "property_account_income_categ_id": "l10n_es.{}_account_full_100".format(
                    new_company_id
                ),
                "property_account_expense_categ_id": "l10n_es.{}_account_full_100".format(
                    new_company_id
                ),
            },
        }.get(account_chart_external_id, False)

        values["property_account_income_categ_id"] = self.env.ref(
            values["property_account_income_categ_id"]
        )
        values["property_account_expense_categ_id"] = self.env.ref(
            values["property_account_expense_categ_id"]
        )
        product_category_company_share.write(values)

    def create_capital_share_product_template(self):
        new_company_id = self.new_company_id.id
        self_new_company = self.with_company(new_company_id)
        # We use sudo to be able to copy the product and not needing to be in the main company
        taxes_id = self.env.ref(
            "l10n_es.{}_account_tax_template_s_iva_ns".format(self.new_company_id.id)
        )
        self.new_product_share_template = self.sudo().product_share_template.copy(
            {
                "name": self.product_share_template.name,
                "company_id": self.new_company_id.id,
                "list_price": self.capital_share,
                "active": True,
                "taxes_id": taxes_id,
            }
        )
        self_new_company.new_company_id.initial_subscription_share_amount = (
            self.capital_share
        )

    def set_cooperative_account(self):
        self_new_company = self.with_company(self.new_company_id)
        new_company = self_new_company.new_company_id
        new_company.write(
            {
                "property_cooperator_account": self.match_account(
                    self.property_cooperator_account
                ).id
            }
        )

    def action_accept(self):
        self.create_company()
        self.control_company_partner_visibility()
        self.add_company_managers()
        self.create_default_utm_stage()
        if self.create_landing:
            self.create_public_data()
        if self.crm_lead_id:
            self.add_company_log()
            self.crm_lead_id.action_set_won_rainbowman()
        if self.hook_cron:
            self.with_delay().thread_action_accept()
        else:
            self.thread_action_accept()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": _("Company creation successful"),
                "message": _("Community creation process has been started."),
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def create_company(self):
        pack_2_tag = self.env.ref("energy_communities.pack_2")
        allow_new_members = False
        if self.crm_lead_id:
            crm_pack_2_tag = self.crm_lead_id.tag_ids.filtered(
                lambda tag: tag.id == pack_2_tag.id
            )
            if crm_pack_2_tag and self.ce_member_status == "open":
                allow_new_members = True
        vat = False
        if self.vat:
            vat = self.vat.replace(" ", "").upper()
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
                    "ce_tag_ids": self.ce_tag_ids,
                }
            )
        )

    def control_company_partner_visibility(self):
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
        new_landing = self.new_company_id.sudo().create_landing()
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
        new_landing.create_landing_place()

    def thread_action_accept(self):
        self.configure_community_accounting()
        self.update_taxes()
        self.update_properties()
        if self.property_cooperator_account:
            self.set_cooperative_account()
        self.update_product_category_company_share()
        self.create_capital_share_product_template()

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
