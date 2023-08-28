import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..pywordpress_client.resources.authenticate import Authenticate
from ..pywordpress_client.resources.landing_page import (
    LandingPage as LandingPageResource,
)

_HIERARCHY_LEVEL_VALUES = [
    ("instance", _("Instance")),
    ("coordinator", _("Coordinator")),
    ("community", _("Community")),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.onchange("hierarchy_level")
    def onchange_hierarchy_level(self):
        self.parent_id = False

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

    hierarchy_level = fields.Selection(
        selection=_HIERARCHY_LEVEL_VALUES,
        required=True,
        string="Hierarchy level",
        default="community",
    )
    parent_id_filtered_ids = fields.One2many(
        "res.company",
        compute=_compute_parent_id_filtered_ids,
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
    landing_page_id = fields.Many2one("landing.page", string=_("Landing Page"))
    wordpress_db_username = fields.Char(string=_("Wordpress DB Admin Username"))
    wordpress_db_password = fields.Char(string=_("Wordpress DB Admin Password"))
    wordpress_base_url = fields.Char(string=_("Wordpress Base URL (JWT auth)"))

    @api.constrains("hierarchy_level", "parent_id")
    def _check_hierarchy_level(self):
        for rec in self:
            if rec.hierarchy_level == "instance":
                if self.search_count(
                    [("hierarchy_level", "=", "instance"), ("id", "!=", rec.id)]
                ):
                    raise ValidationError(_("An instance company already exists"))
                if rec.parent_id:
                    raise ValidationError(
                        _("You cannot create a instance company with a parent company.")
                    )
            if (
                rec.hierarchy_level == "coordinator"
                and rec.parent_id.hierarchy_level != "instance"
            ):
                raise ValidationError(
                    _("Parent company must be instance hierarchy level.")
                )
            if (
                rec.hierarchy_level == "community"
                and rec.parent_id.hierarchy_level != "coordinator"
            ):
                raise ValidationError(
                    _("Parent company must be coordinator hierarchy level.")
                )

    @api.constrains("hierarchy_level", "parent_id")
    def _check_hierarchy_level(self):
        for rec in self:
            if rec.hierarchy_level == "instance":
                if self.search_count(
                    [("hierarchy_level", "=", "instance"), ("id", "!=", rec.id)]
                ):
                    raise ValidationError(_("An instance company already exists"))
                if rec.parent_id:
                    raise ValidationError(
                        _("You cannot create a instance company with a parent company.")
                    )
            if (
                rec.hierarchy_level == "coordinator"
                and rec.parent_id.hierarchy_level != "instance"
            ):
                raise ValidationError(
                    _("Parent company must be instance hierarchy level.")
                )
            if (
                rec.hierarchy_level == "community"
                and rec.parent_id.hierarchy_level != "coordinator"
            ):
                raise ValidationError(
                    _("Parent company must be coordinator hierarchy level.")
                )

    @api.model
    def get_real_ce_company_id(self, api_param_odoo_compant_id):
        if api_param_odoo_compant_id == self.API_PARAM_ID_VALUE_FOR_COORDINADORA:
            return self.search([("coordinator", "=", True)], limit=1) or None
        else:
            return self.search([("id", "=", api_param_odoo_compant_id)]) or None

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

    def get_ce_members(self, domain_key="in_kc_and_active"):
        domains_dict = {
            "in_kc_and_active": [
                ("company_id", "=", self.id),
                ("oauth_uid", "!=", None),
                ("active", "=", True),
            ]
        }
        members = self.env["res.users"].sudo().search(domains_dict["in_kc_and_active"])
        return members

    @api.model
    def _is_not_unique(self, vals):
        # check for VAT
        if vals.get("vat", False) and vals.get("vat"):
            sanit_vat = re.sub(r"[^a-zA-Z0-9]", "", vals["vat"]).lower()
            if sanit_vat in [
                re.sub(r"[^a-zA-Z0-9]", "", c.vat).lower()
                for c in self.search([])
                if c.vat
            ]:
                raise UserError(
                    _(
                        "Unable to create new company because there is an allready existing company with this VAT number: {}"
                    ).format(vals["vat"])
                )

        # check for name
        if vals.get("name", False) and vals.get("name"):
            # sanit_name = slugify(vals['name'])
            sanit_name = vals["name"]
            # if sanit_name in [slugify(c.name) for c in self.search([]) if c.name]:
            if sanit_name in [c.name for c in self.search([]) if c.name]:
                raise UserError(
                    _(
                        "Unable to create new company because there is an allready existing company with this NAME: {}"
                    ).format(vals["name"])
                )

    @api.model
    def create(self, vals):
        # check that we are not creating duplicate companies by vat or by name
        self._is_not_unique(vals)

        new_company = super().create(vals)

        return new_company

    def get_active_services(self):
        """Return a list of dicts with the key data of each active Service"""
        self.ensure_one()
        res = []
        for tag in self.ce_tag_ids:
            res.append({"id": tag.id, "name": tag.name, "ext_id": tag.tag_ext_id})
        return res

    def get_public_web_landing_url(self):
        # TODO: Get from landing page or company, for now we don't need
        return ""

    def get_keycloak_odoo_login_url(self):
        login_provider_id = self.env.ref("energy_communities.keycloak_login_provider")
        return login_provider_id.get_auth_link()

    def create_landing(self):
        landing_page = self.env["landing.page"]
        vals = {"company_id": self.id, "name": self.name, "status": "draft"}
        new_landing = landing_page.create(vals)
        context = {
            "__last_update": {},
            "active_model": "landing.page",
            "active_id": new_landing.id,
        }
        self.write({"landing_page_id": new_landing.id})
        self.action_create_wp_landing()
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "landing.page",
            "res_id": new_landing.id,
            "target": "current",
            "context": context,
        }

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
