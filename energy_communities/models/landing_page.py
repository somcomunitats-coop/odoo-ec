from odoo import models, fields, api, _
from .res_config_settings import ResConfigSettings
from ..pywordpress_client.resources.authenticate import Authenticate
from ..pywordpress_client.resources.landing_page import LandingPage as LandingPageResource


class LandingPage(models.Model):
    _name = "landing.page"

    name = fields.Char(string="Name")
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
    virtual_office_link = fields.Char(string="Virtual office link")
    external_website_link = fields.Char(string="External website link")
    group_image_link = fields.Char(string="Group image link")
    short_description = fields.Char(string="Short description")
    long_description = fields.Text(string="Long description")
    why_become_cooperator = fields.Text(string="Why become cooperator")
    become_cooperator_process = fields.Text(string="Become cooperator process")
    subscription_information = fields.Text(string="Subscription information")
    new_cooperator_form_link = fields.Char(string="New cooperator form link")
    contact_form = fields.Char(string="Contact form")
    subscription_link = fields.Char(string="Subscription link")
    social_media_link = fields.Char(string="Social media link")
    map_geolocation = fields.Char(string="Map geolocation")
    street = fields.Char(string="Street")
    postal_code = fields.Char(string="Postal code")
    city = fields.Char(string="City")
    community_active_services = fields.Many2many(
        string="Community active services", related="company_id.ce_tag_ids"
    )

    def to_dict(self):
        data = {
            "title": self.name or "",
            "odoo_company_id": self.company_id.id,
            "status": self.status,
            "allow_new_members": self.allow_new_members,
            "number_of_members": self.number_of_members,
            "virtual_office_link": self.virtual_office_link or "",
            "external_website_link": self.external_website_link or "",
            "community_active_services": self.community_active_services,
            "group_image_link": self.group_image_link or "",
            "short_description": self.short_description or "",
            "long_description": self.long_description or "",
            "why_become_cooperator": self.why_become_cooperator or "",
            "become_cooperator_process": self.become_cooperator_process or "",
            "subscription_information": self.subscription_information or "",
            "new_cooperator_form_link": self.new_cooperator_form_link or "",
            "contact_form": self.contact_form or "",
            "subscription_link": self.subscription_link or "",
            "social_media_link": self.social_media_link or "",
            "map_geolocation": self.map_geolocation or "",
            "street": self.street or "",
            "postal_code": self.postal_code or "",
            "city": self.city or "",
        }
        return data

    def action_landing_page_status(self):
        for record in self:
            new_status = "draft" if record.status == "publish" else "publish"
            instance_company = self.env['res.company'].search(
                [('hierarchy_level', '=', 'instance')])
            if instance_company:
                username = instance_company.wordpress_db_username
                password = instance_company.wordpress_db_password
                auth = Authenticate(username, password).authenticate()
                token = "Bearer %s" % auth["token"]
                landing_page_data = record.to_dict()
                landing_page_data["status"] = new_status
                landing_page_resource = LandingPageResource(
                    record.wp_landing_page_id)
                landing_page_resource.update(token, landing_page_data)

                record.write({"status": new_status})
