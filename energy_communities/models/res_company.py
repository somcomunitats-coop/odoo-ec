import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..pywordpress_client.resources.authenticate import Authenticate
from ..pywordpress_client.resources.landing_page import (
    LandingPage as LandingPageResource,
)

_HIERARCHY_LEVEL_BASE_VALUES = [
    ("coordinator", _("Coordinator")),
    ("community", _("Community")),
]
_HIERARCHY_LEVEL_VALUES = _HIERARCHY_LEVEL_BASE_VALUES + [("instance", _("Platform"))]

_LEGAL_FORM_VALUES = [
    ("undefined", _("Under definition")),
    ("cooperative", _("Cooperative")),
    ("non_profit", _("Non profit association")),
    ("limited_company", _("Limited company")),
    ("general_partnership", _("General partnership")),
    ("community_of_property", _("community of property")),
    ("limited_partnership", _("Limited partnership")),
    ("stock_company", _("Stock company")),
    ("individual_entrepreneur", _("Individual entrepreneur")),
]

_CE_STATUS_VALUES = [
    ("active", _("active")),
    ("building", _("building")),
]

_CE_MEMBER_STATUS_VALUES = [
    ("open", _("Open")),
    ("closed", _("Closed")),
]
_CE_TYPE = [
    ("citizen", _("Citizen")),
    ("industrial", _("Industrial")),
]


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = ["res.company", "mail.thread", "mail.activity.mixin"]

    hierarchy_level = fields.Selection(
        selection=_HIERARCHY_LEVEL_VALUES,
        required=True,
        string="Hierarchy level",
        default="community",
    )
    parent_id_filtered_ids = fields.One2many(
        "res.company",
        compute="_compute_parent_id_filtered_ids",
        readonly=True,
        store=False,
    )
    ce_tag_ids = fields.Many2many("crm.tag", string="Energy Community Services")
    cooperator_journal = fields.Many2one(
        "account.journal",
        string="Cooperator Journal",
        domain="[('type','=','sale'),('active','=',True)]",
        help="This journal will be"
        " the default one as the"
        " receivable journal for the"
        " cooperators",
    )
    foundation_date = fields.Date("Foundation date")
    social_telegram = fields.Char("Telegram Account")
    initial_subscription_share_amount = fields.Float(
        "Initial Subscription Share Amount", digits="Product Price"
    )
    allow_new_members = fields.Boolean(string="Allow new members", default=True)
    create_user_in_keycloak = fields.Boolean(
        "Create user for keycloak",
        help="Users created by cooperator are pushed automatically to keycloak",
        default=False,
    )
    voluntary_share_id = fields.Many2one(
        comodel_name="product.template",
        domain=[("is_share", "=", True)],
        string="Voluntary share to show on website",
    )
    wordpress_base_url = fields.Char(string=_("Wordpress Base URL (JWT auth)"))
    admins = fields.One2many(
        "res.users",
        string="Community admins",
        compute="_compute_admins",
        readonly=True,
        store=False,
    )
    legal_form = fields.Selection(
        selection=_LEGAL_FORM_VALUES,
        string="Legal form",
    )
    comercial_name = fields.Char(string="Comercial name")
    ce_status = fields.Selection(
        selection=_CE_STATUS_VALUES,
        string="Energy Community state",
    )
    landing_page_id = fields.Many2one("landing.page", string=_("Landing Page"))
    wordpress_db_username = fields.Char(string=_("Wordpress DB Admin Username"))
    wordpress_db_password = fields.Char(string=_("Wordpress DB Admin Password"))
    wordpress_base_url = fields.Char(string=_("Wordpress Base URL (JWT auth)"))
    footer_doc_policy_text = fields.Html(
        string="Footer doc policy text", translate=True
    )
    display_footer_doc_policy_text = fields.Boolean("Display footer doc policy text")
    footer_doc_policy_text = fields.Html(
        string="Footer doc policy text", translate=True
    )
    display_footer_doc_policy_text = fields.Boolean("Display footer doc policy text")
    voluntary_share_form_header_text = fields.Html(
        string="Voluntary share form header text", translate=True
    )
    cooperator_share_form_header_text = fields.Html(
        string="Cooperator share form header text", translate=True
    )
    notify_to_coord_child_ccee_submissions = fields.Boolean(
        string=_("Notify the Coordinator of new Subscriptions of their CCEE"),
        help=_(
            "If it is checked, the Coordinator will receive a copy of each auto-response email that is generated in any of its CCEE when a new Member Subscription request is received."
        ),
    )

    # COMPUTED FIELDS
    @api.depends("hierarchy_level")
    def _compute_parent_id_filtered_ids(self):
        for rec in self:
            if rec.hierarchy_level == "instance":
                rec.parent_id_filtered_ids = False
            elif rec.hierarchy_level == "coordinator":
                rec.parent_id_filtered_ids = self.search(
                    [("hierarchy_level", "=", "instance")]
                )
            elif rec.hierarchy_level == "community":
                rec.parent_id_filtered_ids = self.search(
                    [("hierarchy_level", "=", "coordinator")]
                )

    def _compute_admins(self):
        for rec in self:
            role_name = rec._get_admin_role_name_from_hierarchy_level()
            role_lines = self.env["res.users.role.line"].search(
                [
                    ("company_id.id", "=", rec.id),
                    ("active", "=", True),
                    ("role_id.code", "=", role_name),
                ]
            )
            rec.admins = role_lines.mapped("user_id")

    # ONCHANGE ACTIONS
    @api.onchange("hierarchy_level")
    def onchange_hierarchy_level(self):
        self.parent_id = False

    # CONSTRAINS
    @api.constrains("name", "vat")
    def _check_uniqueness(self):
        for rec in self:
            rec._validate_uniqueness()

    @api.constrains("hierarchy_level", "parent_id", "partner_id")
    def _check_hierarchy_level(self):
        for rec in self:
            rec._validate_hierarchy()
            rec.partner_id.compute_company_hierarchy_level()

    # VALIDATION
    def _validate_hierarchy(self):
        if self.hierarchy_level == "instance":
            if self.search_count(
                [("hierarchy_level", "=", "instance"), ("id", "!=", self.id)]
            ):
                raise ValidationError(_("An instance company already exists"))
            if self.parent_id:
                raise ValidationError(
                    _("You cannot create a instance company with a parent company.")
                )
        if (
            self.hierarchy_level == "coordinator"
            and self.parent_id.hierarchy_level != "instance"
        ):
            raise ValidationError(_("Parent company must be instance hierarchy level."))
        if (
            self.hierarchy_level == "community"
            and self.parent_id.hierarchy_level != "coordinator"
        ):
            raise ValidationError(
                _("Parent company must be coordinator hierarchy level.")
            )

    def _validate_uniqueness(self):
        # check for VAT
        if self.vat:
            sanit_vat = re.sub(r"[^a-zA-Z0-9]", "", self.vat).upper()
            if sanit_vat in [
                re.sub(r"[^a-zA-Z0-9]", "", c.vat).upper()
                for c in self.env["res.company"].search([("id", "!=", self.id)])
                if c.vat
            ]:
                raise UserError(
                    _(
                        "Unable to create new company because there is an allready existing company with this VAT number: {}"
                    ).format(self.vat)
                )
        # check for name
        if self.name:
            existing_company = self.env["res.company"].search(
                [
                    ("id", "!=", self.id),
                    ("name", "=", self.name),
                ]
            )
            if existing_company:
                raise UserError(
                    _(
                        "Unable to create new company because there is an allready existing company with this NAME: {}"
                    ).format(self.name)
                )

    # GETTERS
    def _get_admin_role_name_from_hierarchy_level(self):
        if self.hierarchy_level == "community":
            return "role_ce_admin"
        elif self.hierarchy_level == "coordinator":
            return "role_coord_admin"
        elif self.hierarchy_level == "instance":
            return "role_platform_admin"

    def get_ce_members(self, domain_key="in_kc_and_active"):
        domains_dict = {
            "in_kc_and_active": [
                ("company_id", "=", self.id),
                ("oauth_uid", "!=", None),
                ("active", "=", True),
            ]
        }
        return self.env["res.users"].sudo().search(domains_dict["in_kc_and_active"])

    def get_users(self, role_codes=False):
        role_codes = role_codes or []
        if role_codes:
            users = (
                self.env["res.users.role.line"]
                .sudo()
                .search(
                    [
                        ("company_id", "=", self.id),
                        ("role_id.code", "in", role_codes),
                    ]
                )
                .user_id
            )
        else:
            users = (
                self.env["res.users.role.line"]
                .sudo()
                .search(
                    [
                        ("company_id", "=", self.id),
                    ]
                )
                .user_id
            )
        wants_platform_admins = (
            self.env.ref("energy_communities.role_platform_admin").code in role_codes
            or not role_codes
        )
        if wants_platform_admins:
            users += (
                self.env["res.users.role.line"]
                .sudo()
                .search(
                    [
                        (
                            "role_id",
                            "=",
                            self.env.ref("energy_communities.role_platform_admin").id,
                        ),
                    ]
                )
                .user_id
            )
        return users

    def get_active_services(self):
        """Return a list of dicts with the key data of each active Service"""
        self.ensure_one()
        res = []
        for tag in self.ce_tag_ids:
            res.append({"id": tag.id, "name": tag.name, "ext_id": tag.tag_ext_id})
        return res

    def get_lower_hierarchy_level(self):
        if self.hierarchy_level == "instance":
            return "coordinator"
        elif self.hierarchy_level == "coordinator":
            return "community"
        return ""

    def get_child_companies(self):
        return self.env["res.company"].search(
            [
                ("hierarchy_level", "=", self.get_lower_hierarchy_level()),
                ("parent_id", "=", self.id),
            ]
        )

    def get_public_web_landing_url(self):
        # TODO: Get from landing page or company, for now we don't need
        return ""

    def get_keycloak_odoo_login_url(self):
        login_provider_id = self.env.ref("energy_communities.keycloak_login_provider")
        return login_provider_id.get_auth_link()

    # LANDING
    def action_create_landing(self):
        new_landing = self.create_landing()
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "landing.page",
            "res_id": new_landing.id,
            "target": "current",
            "context": context,
        }

    def create_landing(self):
        landing_page = self.env["landing.page"]
        vals = {"company_id": self.id, "name": self.comercial_name, "status": "draft"}
        new_landing = landing_page.create(vals)
        context = {
            "__last_update": {},
            "active_model": "landing.page",
            "active_id": new_landing.id,
        }
        self.write({"landing_page_id": new_landing.id})
        self.action_create_wp_landing()
        return new_landing

    def action_create_wp_landing(self, fields=None):
        instance_company = self.env["res.company"].search(
            [("hierarchy_level", "=", "instance")]
        )
        if instance_company:
            baseurl = instance_company.wordpress_base_url
            username = instance_company.wordpress_db_username
            password = instance_company.wordpress_db_password
            auth = Authenticate(baseurl, username, password).authenticate()
            token = "Bearer %s" % auth["token"]
            landing_page_data = self.landing_page_id.to_dict()
            landing_page = LandingPageResource(token, baseurl).create(landing_page_data)
            self.landing_page_id.write({"wp_landing_page_id": landing_page["id"]})

    def get_landing_page_form(self):
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "landing.page",
            "res_id": self.landing_page_id.id,
            "target": "current",
        }

    # TODO: Unused functions. Delete if really not needed.
    def check_ce_has_admin(self):
        self.ensure_one()
        admin_roles_ids = [
            r["odoo_role_id"]
            for r in self.env["res.users"].ce_user_roles_mapping().values()
            if r["is_admin"]
        ]
        company_user_ids = self.get_ce_members().ids
        admins_user_ids = []
        for admin_role in self.env["res.users.role"].sudo().browse(admin_roles_ids):
            for role_line in admin_role.line_ids:
                admins_user_ids.append(role_line.user_id.id)
        return any([user in admins_user_ids for user in company_user_ids])
