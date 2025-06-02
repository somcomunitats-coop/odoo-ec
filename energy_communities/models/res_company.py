import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..client_map.config import LandingClientConfig
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

    def _get_logo(self):
        return super()._get_logo()

    logo = fields.Image(default=_get_logo, string="Company Logo")
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
    foundation_date = fields.Date("Foundation date")
    social_telegram = fields.Char("Telegram Account")
    allow_new_members = fields.Boolean(string="Allow new members", default=True)
    create_user_in_keycloak = fields.Boolean(
        "Create user for keycloak",
        help="Users created by cooperator are pushed automatically to keycloak",
        default=False,
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
    website_id = fields.Many2one("website", store=False, compute="_compute_website_id")
    landing_page_status = fields.Selection(related="landing_page_id.status")
    wordpress_db_username = fields.Char(string=_("Wordpress DB Admin Username"))
    wordpress_db_password = fields.Char(string=_("Wordpress DB Admin Password"))
    wordpress_base_url = fields.Char(string=_("Wordpress Base URL (JWT auth)"))
    notify_to_coord_child_ccee_submissions = fields.Boolean(
        string=_("Notify the Coordinator of new Subscriptions of their CCEE"),
        help=_(
            "If it is checked, the Coordinator will receive a copy of each auto-response email that is generated in any of its CCEE when a new Member Subscription request is received."
        ),
    )
    available_role_ids = fields.One2many(
        "res.users.role",
        string="Available roles",
        compute="_compute_parent_id_filtered_ids",
    )
    community_energy_action_ids = fields.One2many(
        "community.energy.action", "company_id", string="Community energy actions"
    )

    # COMPUTED FIELDS
    def _compute_website_id(self):
        for rec in self:
            rec.website_id = False
            rel_website = self.env["website"].search([("company_id", "=", rec.id)])
            if rel_website:
                rec.website_id = rel_website[0].id

    @api.depends("hierarchy_level")
    def _compute_parent_id_filtered_ids(self):
        for rec in self:
            if rec.hierarchy_level == "instance":
                rec.parent_id_filtered_ids = False
                rec.available_role_ids = [
                    (4, self.env.ref("energy_communities.role_platform_admin").id)
                ]
            elif rec.hierarchy_level == "coordinator":
                rec.parent_id_filtered_ids = self.search(
                    [("hierarchy_level", "=", "instance")]
                )
                rec.available_role_ids = [
                    (4, self.env.ref("energy_communities.role_coord_admin").id),
                ]
            elif rec.hierarchy_level == "community":
                rec.parent_id_filtered_ids = self.search(
                    [("hierarchy_level", "=", "coordinator")]
                )
                rec.available_role_ids = [
                    (4, self.env.ref("energy_communities.role_ce_manager").id),
                    (4, self.env.ref("energy_communities.role_ce_admin").id),
                    (4, self.env.ref("energy_communities.role_ce_member").id),
                ]

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
    def get_become_cooperator_button_label(self, mode, lang):
        return LandingClientConfig.COOPERATOR_BUTTON_LABEL_CONFIG[mode][lang]

    def get_become_cooperator_button_link(self, mode, lang):
        return LandingClientConfig.COOPERATOR_BUTTON_URL_CONFIG[mode].format(
            base_url=self.env["ir.config_parameter"].get_param("web.base.url"),
            lang=lang,
            odoo_company_id=self.id,
        )

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

    def get_energy_actions_dict_list(self):
        """Return a list of dicts with the key data of each energy action"""
        self.ensure_one()
        res = []
        for energy_action in self.community_energy_action_ids:
            if energy_action.public_status == "published":
                res.append(
                    {
                        "id": energy_action.energy_action_id.id,
                        "name": energy_action.energy_action_id.name,
                        "ext_id": energy_action.energy_action_id.xml_id,
                    }
                )
        return res

    def get_all_energy_actions_dict_list(self):
        """Return all energy actions for the current energy community"""
        self.ensure_one()
        energy_actions = self.env["energy.action"].search([])
        published_energy_actions_ids = set(
            self.community_energy_action_ids.filtered_domain(
                [("public_status", "=", "published")]
            ).energy_action_id.ids
        )
        res = [
            {
                "id": energy_action.id,
                "name": energy_action.name,
                "ext_id": energy_action.xml_id,
                "is_active": energy_action.id in published_energy_actions_ids,
            }
            for energy_action in energy_actions
        ]
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

    def company_hierarchy_level_url(self):
        if self.hierarchy_level == "coordinator":
            return "rest-ce-coord"
        else:
            return "rest-ce-landing"

    # WEBSITE
    def action_create_website(self):
        for rec in self:
            website = self.env["website"]
            vals = {
                "company_id": rec.id,
                "name": rec.name,
                # "user_id": self.env.user.id
            }
            new_website = website.create(vals)
            return self.get_website_form()

    # LANDING
    def action_create_landing(self):
        if not self.comercial_name:
            raise ValidationError(
                _(
                    "Company comercial name must be established in order to create a landing"
                )
            )
        new_landing = self.action_create_odoo_landing()
        self.action_create_wp_landing()
        return new_landing

    def action_create_odoo_landing(self):
        landing_page = self.env["landing.page"]
        vals = {"company_id": self.id, "name": self.comercial_name, "status": "draft"}
        new_landing = landing_page.create(vals)
        new_landing.setup_slug_id()
        if self.hierarchy_level == "coordinator":
            new_landing.sudo().create_or_update_and_apply_coordinator_filter()
        self.write({"landing_page_id": new_landing.id})
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
            landing_page = LandingPageResource(
                token, baseurl, self.company_hierarchy_level_url()
            ).create(landing_page_data)
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

    def get_website_form(self):
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "website",
            "res_id": self.website_id.id,
            "target": "current",
        }

    # CHANGE COORDINATOR
    def action_open_change_coordinator_wizard(self):
        wizard = self.env["change.coordinator.wizard"].create({})
        return {
            "type": "ir.actions.act_window",
            "name": _("Change coordinator"),
            "res_model": "change.coordinator.wizard",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }

    def change_coordinator(self, incoming_coordinator, change_reason):
        outgoing_coordinator = self.parent_id
        if incoming_coordinator.id != outgoing_coordinator.id:
            # Change parent_id
            self.write({"parent_id": incoming_coordinator.id})
            # Add coordinator_destination visibility to company's related contact
            self.partner_id.write({"company_ids": [(4, incoming_coordinator.id)]})
            # Adjust related community place coordinator-filtering
            self._adjust_related_map_place_filtering(
                outgoing_coordinator, incoming_coordinator
            )
            # Sanitize related users roles
            self._sanitize_outgoing_coordinator_users(outgoing_coordinator)
            self._sanitize_incoming_coordinator_users(incoming_coordinator)
            # leave message on chatter
            self._log_change_coordinator(
                incoming_coordinator, outgoing_coordinator, change_reason
            )

    def _log_change_coordinator(
        self, incoming_coordinator, outgoing_coordinator, change_reason
    ):
        message = _(
            "There has been a coordinator change \
            from [OLD:{outgoing_id}] {outgoing_name} to [NEW:{incoming_id}] {incoming_name}, \
            Change reason: {change_reason}"
        ).format(
            outgoing_id=outgoing_coordinator.id,
            outgoing_name=outgoing_coordinator.name,
            incoming_id=incoming_coordinator.id,
            incoming_name=incoming_coordinator.name,
            change_reason=change_reason,
        )
        self.message_post(
            subject="[COORD_CHANGE]",
            body=message,
        )

    def _adjust_related_map_place_filtering(
        self, outgoing_coordinator, incoming_coordinator
    ):
        community_landing_page = self.landing_page_id
        if community_landing_page:
            filter_coord_arr = []
            outgoing_coord_filter = (
                community_landing_page.get_map_coordinator_filter_in_related_place(
                    outgoing_coordinator
                )
            )
            if outgoing_coord_filter:
                filter_coord_arr.append((3, outgoing_coord_filter.id))
            incoming_coord_filter = (
                community_landing_page.get_map_coordinator_filter_in_related_place(
                    incoming_coordinator
                )
            )
            if (
                incoming_coord_filter
                and incoming_coordinator.landing_page_status == "publish"
            ):
                filter_coord_arr.append((4, incoming_coord_filter.id))
            if community_landing_page.map_place_ids and filter_coord_arr:
                for place in community_landing_page.map_place_ids:
                    place.sudo().write({"filter_mids": filter_coord_arr})

    def _sanitize_outgoing_coordinator_users(self, outgoing_coordinator):
        coord_users = outgoing_coordinator.get_users(["role_coord_admin"])
        if coord_users:
            for user in coord_users:
                # remove community manager role for the outgoing coordinator admins/managers
                outgoing_user_manager_roles = user.get_user_role_lines(
                    company_id=self.id, role_codes=["role_ce_manager"]
                )
                if outgoing_user_manager_roles:
                    for role in outgoing_user_manager_roles:
                        role.unlink()
                # remove access to community for the outgoing coordinator admins/managers if needed
                outgoing_user_roles = user.get_user_role_lines(company_id=self.id)
                if not outgoing_user_roles:
                    user.write({"company_ids": [(3, self.id)]})

    def _sanitize_incoming_coordinator_users(self, incoming_coordinator):
        coord_users = incoming_coordinator.get_users(["role_coord_admin"])
        if coord_users:
            for user in coord_users:
                # Add community manager role for the incoming coordinator admins/workers
                # Add access to community for the incoming coordinator admins/workers
                user.make_ce_user(self.id, "role_ce_manager")
