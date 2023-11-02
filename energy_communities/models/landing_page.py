from datetime import datetime

from odoo import _, api, fields, models

from ..pywordpress_client.resources.authenticate import Authenticate
from ..pywordpress_client.resources.landing_page import (
    LandingPage as LandingPageResource,
)
from .res_config_settings import ResConfigSettings


class LandingPage(models.Model):
    _name = "landing.page"

    name = fields.Char(string="Name", translate=True)
    company_id = fields.Many2one("res.company", string="Company")
    wp_landing_page_id = fields.Integer(string="WP Landing Page")
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
    # TODO: group_image_link Left for backward compatibility. To be removed
    group_image_link = fields.Char(string="Group image link")
    primary_image_file = fields.Image("Primary Image")
    secondary_image_file = fields.Image("Secondary Image")
    short_description = fields.Text(string="Short description", translate=True)
    long_description = fields.Text(string="Long description", translate=True)
    why_become_cooperator = fields.Html(string="Why become cooperator", translate=True)
    become_cooperator_process = fields.Html(
        string="Become cooperator process", translate=True
    )
    # TODO: remove this one
    map_geolocation = fields.Char(string="Map geolocation")
    map_place_id = fields.Many2one("cm.place", "Place reference")
    street = fields.Char(string="Street")
    postal_code = fields.Char(string="Postal code")
    city = fields.Char(string="City")
    community_active_services = fields.Many2many(
        string="Community active services", related="company_id.ce_tag_ids"
    )
    community_type = fields.Selection(
        selection=[("citizen", _("Citizen")), ("industrial", _("Industrial"))],
        default="citizen",
        required=True,
        string="Community type",
    )
    community_secondary_type = fields.Selection(
        selection=[("cooperative", _("Cooperative"))],
        default="cooperative",
        required=True,
        string="Community secondary type",
    )
    community_status = fields.Selection(
        selection=[("open", _("Open")), ("closed", _("Closed"))],
        default="open",
        required=True,
        string="Community status",
    )
    wp_lastupdate_datetime = fields.Datetime(string="Last wordpress update date")

    def _get_image_attachment(self, field_name):
        file_attachment = self.env["ir.attachment"].search(
            [
                ("res_id", "=", self.id),
                ("res_model", "=", "landing.page"),
                ("res_field", "=", field_name),
            ]
        )
        return file_attachment

    def _get_image_write_date(self, field_name):
        file_write_date = ""
        file_attachment = self._get_image_attachment(field_name)
        if file_attachment:
            file_write_date = str(file_attachment.write_date)
        return file_write_date

    def _get_image_extension(self, field_name):
        file_write_date = ""
        file_attachment = self._get_image_attachment(field_name)
        extension = ""
        if file_attachment:
            extension = file_attachment.mimetype.split("/")[1]
        return extension

    def _get_image_payload(self, field_name):
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
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
            + self._get_image_extension(field_name)
        )

    def to_dict(self):
        if self.primary_image_file:
            primary_image_file = self._get_image_payload("primary_image_file")
            primary_image_file_write_date = self._get_image_write_date(
                "primary_image_file"
            )
        else:
            primary_image_file = ""
            primary_image_file_write_date = ""
        if self.secondary_image_file:
            secondary_image_file = self._get_image_payload("secondary_image_file")
            secondary_image_file_write_date = self._get_image_write_date(
                "secondary_image_file"
            )
        else:
            secondary_image_file = ""
            secondary_image_file_write_date = ""
        if self.map_place_id:
            map_reference = self.map_place_id.slug_id
        else:
            map_reference = ""
        if self.why_become_cooperator == "<p><br></p>":
            self.why_become_cooperator = ""
        if self.become_cooperator_process == "<p><br></p>":
            self.become_cooperator_process = ""
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
                "community_status": self.community_status,
                "allow_new_members": self.allow_new_members,
                "number_of_members": self.number_of_members,
                "external_website_link": self.external_website_link or "",
                "twitter_link": self.twitter_link or "",
                "instagram_link": self.instagram_link or "",
                "telegram_link": self.telegram_link or "",
                "community_active_services": self.company_id.get_active_services(),
                # TODO: group_image_link Left for backward compatibility. To be removed
                "group_image_link": self.group_image_link or "",
                "primary_image_file": primary_image_file,
                "primary_image_file_write_date": primary_image_file_write_date,
                "secondary_image_file": secondary_image_file,
                "secondary_image_file_write_date": secondary_image_file_write_date,
                "short_description": self.short_description or "",
                "long_description": self.long_description or "",
                "why_become_cooperator": self.why_become_cooperator,
                "become_cooperator_process": self.become_cooperator_process,
                "map_geolocation": self.map_geolocation or "",
                "map_reference": map_reference,
                "street": self.street or "",
                "postal_code": self.postal_code or "",
                "city": self.city or "",
            }
        }

    def action_landing_page_status(self):
        for record in self:
            new_status = "draft" if record.status == "publish" else "publish"
            record.write({"status": new_status})

    def action_update_wp(self):
        for record in self:
            record._update_wordpress()

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
            LandingPageResource(token, baseurl, self.wp_landing_page_id).update(
                landing_page_data
            )
            self.write({"wp_lastupdate_datetime": datetime.now()})
