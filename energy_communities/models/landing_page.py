from datetime import datetime

from odoo import _, api, fields, models

from odoo.addons.energy_communities.utils import get_translation

from ..client_map.config import MapClientConfig
from ..client_map.resources.landing_cmplace import (
    LandingCmPlace as LandingCmPlaceResource,
)
from ..pywordpress_client.resources.authenticate import Authenticate
from ..pywordpress_client.resources.landing_page import (
    LandingPage as LandingPageResource,
)
from ..utils import get_successful_popup_message
from .res_company import _CE_MEMBER_STATUS_VALUES, _CE_TYPE, _LEGAL_FORM_VALUES


class LandingPage(models.Model):
    _name = "landing.page"
    _description = "Landing page"

    _inherit = ["cm.coordinates.mixin", "cm.slug.id.mixin"]

    # overwrite models to be check for slug uniqueness. No other landings with same slug_id
    _slug_models = ["landing.page"]

    name = fields.Char(string="Name", translate=True)
    company_id = fields.Many2one("res.company", string="Company")
    wp_landing_page_id = fields.Integer(string="WP Landing Page")
    wp_sync_mode = map_sync_mode = fields.Selection(
        [("none", _("None")), ("update", _("Update"))],
        compute="_compute_wp_sync_mode",
        store=False,
    )
    status = fields.Selection(
        selection=[("draft", _("Draft")), ("publish", _("Publish"))],
        default="draft",
        required=True,
        string="Status",
    )
    allow_new_members = fields.Boolean(
        string="Allows new members", related="company_id.allow_new_members"
    )
    number_of_members = fields.Integer(string="Number of members")
    external_website_link = fields.Char(string="External website link", translate=True)
    twitter_link = fields.Char(
        string="Twitter link", related="company_id.social_twitter"
    )
    telegram_link = fields.Char(
        string="Telegram link", related="company_id.social_telegram"
    )
    instagram_link = fields.Char(
        string="Instagram link", related="company_id.social_instagram"
    )
    primary_image_file = fields.Image("Primary Image")
    secondary_image_file = fields.Image("Secondary Image")
    short_description = fields.Text(string="Short description", translate=True)
    long_description = fields.Text(string="Long description", translate=True)
    why_become_cooperator = fields.Html(string="Why become cooperator", translate=True)
    become_cooperator_process = fields.Html(
        string="Become cooperator process", translate=True
    )
    map_place_ids = fields.One2many("cm.place", "landing_id", string="Place references")
    map_sync_mode = fields.Selection(
        [("create", _("Create")), ("update", _("Update"))],
        compute="_compute_map_sync_mode",
        store=False,
    )
    street = fields.Char(string="Street")
    postal_code = fields.Char(string="Postal code")
    city = fields.Char(string="City")
    community_energy_action_ids = fields.One2many(
        "community.energy.action", related="company_id.community_energy_action_ids"
    )
    community_type = fields.Selection(
        selection=_CE_TYPE,
        default="citizen",
        required=True,
        string="Community type",
    )
    # TODO: Get legal form from company. Requires migration script and adjust API
    community_secondary_type = fields.Selection(
        selection=_LEGAL_FORM_VALUES,
        default="cooperative",
        required=True,
        string="Community secondary type",
    )
    community_status = fields.Selection(
        selection=_CE_MEMBER_STATUS_VALUES,
        default="open",
        required=True,
        string="Community status",
    )
    publicdata_lastupdate_datetime = fields.Datetime(
        string="Last wordpress/map update date"
    )
    show_web_link_on_header = fields.Boolean(
        string=_("Show external website link also in header"), default=False
    )
    show_newsletter_form = fields.Boolean(string=_("Show newsletter form"))
    awareness_services = fields.Text(
        string=_("Services to raise awareness in the creation of CCEE"), translate=True
    )
    design_services = fields.Text(
        string=_("Services for the design and implementation of CCEE"), translate=True
    )
    management_services = fields.Text(
        string=_("CCEE management services"), translate=True
    )
    company_logo = fields.Image(string=_("Company logo"), related="company_id.logo")
    hierarchy_level = fields.Selection(
        string="Hierarchy level",
        related="company_id.hierarchy_level",
    )
    parent_id = fields.Many2one(
        "res.company",
        string="Parent Company",
        related="company_id.parent_id",
    )
    parent_landing_id = fields.Many2one(
        "landing.page",
        string="Parent landing page",
        related="company_id.parent_id.landing_page_id",
    )
    cooperator_button_ids = fields.One2many(
        "landing.cooperator.button", "landing_page_id", string="Cooperator buttons"
    )

    @api.depends("map_place_ids")
    def _compute_map_sync_mode(self):
        for record in self:
            if record.map_place_ids:
                record.map_sync_mode = "update"
            else:
                record.map_sync_mode = "create"

    @api.depends("wp_landing_page_id")
    def _compute_wp_sync_mode(self):
        for record in self:
            if record.wp_landing_page_id:
                record.wp_sync_mode = "update"
            else:
                record.wp_sync_mode = "none"

    def _get_image_attachment(self, field_name, query):
        if not query:
            query = [
                ("res_id", "=", self.id),
                ("res_model", "=", "landing.page"),
                ("res_field", "=", field_name),
            ]
        file_attachment = self.env["ir.attachment"].sudo().search(query)
        return file_attachment

    def _get_image_write_date(self, field_name, query=False):
        file_write_date = ""
        file_attachment = self._get_image_attachment(field_name, query)
        if file_attachment:
            file_write_date = str(file_attachment.write_date)
        return file_write_date

    def _get_image_extension(self, field_name, query):
        file_attachment = self._get_image_attachment(field_name, query)
        extension = ""
        if file_attachment:
            extension = file_attachment.mimetype.split("/")[1]
        return extension

    def _get_image_payload(self, field_name, query=False):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return (
            base_url
            + "/web/image/landing.page/"
            + str(self.id)
            + "/"
            + field_name
            + "/"
            + str(self.id)
            + "-"
            + field_name
            + "."
            + self._get_image_extension(field_name, query)
        )

    def to_dict(self):
        # TODO: Refactor this image processing. Build it into a method
        # images
        # company logo
        if self.company_logo:
            attachment_query = [
                ("res_id", "=", self.company_id.id),
                ("res_model", "=", "res.company"),
                ("res_field", "=", "logo"),
            ]
            company_logo = self._get_image_payload("company_logo", attachment_query)
            company_logo_write_date = self._get_image_write_date(
                "company_logo", attachment_query
            )
        else:
            company_logo = ""
            company_logo_write_date = ""
        # primary image
        if self.primary_image_file:
            primary_image_file = self._get_image_payload("primary_image_file")
            primary_image_file_write_date = self._get_image_write_date(
                "primary_image_file"
            )
        else:
            primary_image_file = ""
            primary_image_file_write_date = ""
        # secondary image
        if self.secondary_image_file:
            secondary_image_file = self._get_image_payload("secondary_image_file")
            secondary_image_file_write_date = self._get_image_write_date(
                "secondary_image_file"
            )
        else:
            secondary_image_file = ""
            secondary_image_file_write_date = ""
        # place_reference
        return {
            "landing": {
                "id": self.id,
                "name": self.name,
                "title": self.name,
                "odoo_company_id": self.company_id.id,
                "company_id": self.company_id.id,
                "wp_landing_page_id": self.wp_landing_page_id,
                "status": self.status,
                "community_type": self.community_type,
                "community_secondary_type": self.community_secondary_type,
                # TODO: review this weird way of getting a translation. Why not by API header context lang?
                "legal_form": get_translation(
                    source=dict(_LEGAL_FORM_VALUES)[self.community_secondary_type],
                    lang=self.env.context["lang"],
                    mods="energy_communities",
                ),
                "community_status": self.community_status,
                "allow_new_members": self.allow_new_members,
                "number_of_members": self.number_of_members,
                "external_website_link": self.external_website_link or "",
                "show_web_link_on_header": self.show_web_link_on_header,
                "show_newsletter_form": self.show_newsletter_form,
                "twitter_link": self.twitter_link or "",
                "instagram_link": self.instagram_link or "",
                "telegram_link": self.telegram_link or "",
                "energy_actions": self.company_id.sudo().get_energy_actions_dict_list(),
                "primary_image_file": primary_image_file,
                "primary_image_file_write_date": primary_image_file_write_date,
                "secondary_image_file": secondary_image_file,
                "secondary_image_file_write_date": secondary_image_file_write_date,
                "company_logo": company_logo,
                "company_logo_write_date": company_logo_write_date,
                "short_description": self.short_description or "",
                "long_description": self.long_description or "",
                "why_become_cooperator": ""
                if self.why_become_cooperator == "<p><br></p>"
                or not self.why_become_cooperator
                else self.why_become_cooperator,
                "become_cooperator_process": ""
                if self.become_cooperator_process == "<p><br></p>"
                or not self.become_cooperator_process
                else self.become_cooperator_process,
                "cooperator_buttons": self._get_become_cooperator_button_list(),
                "map_reference": self.slug_id or "",
                "street": self.street or "",
                "postal_code": self.postal_code or "",
                "city": self.city or "",
                "slug_id": self.slug_id or "",
                "display_map": self._must_display_map(),
                "awareness_services": self.awareness_services or "",
                "design_services": self.design_services or "",
                "management_services": self.management_services or "",
            }
        }

    def _get_become_cooperator_button_list(self):
        button_list = []
        for coop_button in self.cooperator_button_ids.filtered(
            lambda button: button.visibility == "visible"
        ):
            button_list.append(coop_button.to_dict())
        return button_list

    def _must_display_map(self):
        if self.hierarchy_level == "coordinator":
            rel_filter = self.env["cm.filter"].search([("landing_id", "=", self.id)])
            if rel_filter:
                return rel_filter.has_related_places(
                    self.env.ref("energy_communities.map_campanya").id
                )
        return False

    def action_landing_page_status(self):
        for record in self:
            new_status = "draft" if record.status == "publish" else "publish"
            record.write({"status": new_status})

    def action_create_landing_place(self):
        for record in self:
            record.sudo().create_landing_place()

    def action_update_public_data(self):
        for record in self:
            record._update_wordpress()
            record.update_map_place()
            record.write({"publicdata_lastupdate_datetime": datetime.now()})
            return get_successful_popup_message(
                _("Public data update successful"),
                _("Wordpress landing and map place has been successfully updated."),
            )

    def _update_wordpress(self):
        instance_company = self.env["res.company"].search(
            [("hierarchy_level", "=", "instance")]
        )
        if instance_company:
            baseurl = instance_company.wordpress_base_url
            username = instance_company.wordpress_db_username
            password = instance_company.wordpress_db_password
            auth = Authenticate(baseurl, username, password).authenticate()
            token = "Bearer %s" % auth["token"]
            landing_page_data = self.to_dict()
            LandingPageResource(
                token,
                baseurl,
                self.company_hierarchy_level_url(),
                self.wp_landing_page_id,
            ).update(landing_page_data)

    def update_map_place(self):
        if self.map_place_ids:
            self.sudo()._update_landing_place()
        if self.hierarchy_level == "coordinator":
            if self.status == "publish":
                self.sudo().create_or_update_and_apply_coordinator_filter()
            else:
                self.sudo().remove_coordinator_filter_to_existing_communities()

    def create_landing_place(self):
        LandingCmPlaceResource(self).create()
        return True

    def update_landing_place(self):
        return self._update_landing_place()

    def _update_landing_place(self):
        LandingCmPlaceResource(self).update()
        return True

    def company_hierarchy_level_url(self):
        if self.hierarchy_level == "coordinator":
            return "rest-ce-coord"
        else:
            return "rest-ce-landing"

    def get_map_coordinator_filter_in_related_place(self, coordinator=False):
        if not coordinator:
            if self.parent_id:
                coordinator = self.parent_id
        if self.hierarchy_level == "community" and coordinator:
            if coordinator.landing_page_id:
                coordinator_filter_group = self.env.ref(
                    "energy_communities.map_filter_group_coordinator"
                )
                return self.env["cm.filter"].search(
                    [
                        ("landing_id", "=", coordinator.landing_page_id.id),
                        ("filter_group_id", "=", coordinator_filter_group.id),
                    ]
                )
        return False

    def create_or_update_and_apply_coordinator_filter(self):
        self.create_or_update_map_coordinator_filter()
        self.apply_coordinator_filter_to_existing_communities()

    def create_or_update_map_coordinator_filter(self):
        coordinator_filter_group = self.env.ref(
            "energy_communities.map_filter_group_coordinator"
        )
        related_filter = self.env["cm.filter"].search(
            [
                ("landing_id", "=", self.id),
                ("filter_group_id", "=", coordinator_filter_group.id),
            ]
        )
        if not related_filter:
            related_filter = self.env["cm.filter"].create(
                {
                    "name": self.name,
                    "icon": "house_user",
                    "color": "brand",
                    "marker_color": MapClientConfig.FILTER_COLOR_CONFIG["marker_color"],
                    "slug_id": self.slug_id,
                    "marker_text_color": MapClientConfig.FILTER_COLOR_CONFIG[
                        "marker_text_color"
                    ],
                    "marker_bg_color": MapClientConfig.FILTER_COLOR_CONFIG[
                        "marker_bg_color"
                    ],
                    "marker_border_color": MapClientConfig.FILTER_COLOR_CONFIG[
                        "marker_border_color"
                    ],
                    "landing_id": self.id,
                    "filter_group_id": coordinator_filter_group.id,
                }
            )
            # related_filter.setup_slug_id()
        else:
            related_filter.write(
                {
                    "name": self.name,
                    "slug_id": self.slug_id,
                }
            )

    def apply_coordinator_filter_to_existing_communities(self):
        self.setup_coordinator_filter_to_existing_communities("apply")

    def remove_coordinator_filter_to_existing_communities(self):
        self.setup_coordinator_filter_to_existing_communities("remove")

    def setup_coordinator_filter_to_existing_communities(self, type):
        existing_communities = self.env["res.company"].search(
            [
                ("parent_id", "=", self.company_id.id),
                ("hierarchy_level", "=", "community"),
            ]
        )
        for community in existing_communities:
            if community.landing_page_id:
                if community.landing_page_id.map_place_ids:
                    related_coordinator_filter = community.landing_page_id.get_map_coordinator_filter_in_related_place(
                        self.company_id
                    )
                    if related_coordinator_filter:
                        if type == "apply":
                            mode = 4
                        if type == "remove":
                            mode = 3
                        for place in community.landing_page_id.map_place_ids:
                            place.write(
                                {"filter_mids": [(mode, related_coordinator_filter.id)]}
                            )
