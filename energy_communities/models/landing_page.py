from odoo import models, fields, api, _
from .res_config_settings import ResConfigSettings
from ..pywordpress_client.resources.authenticate import Authenticate
from ..pywordpress_client.resources.landing_page import LandingPage as LandingPageResource


class LandingPage(models.Model):
    _name = "landing.page"

    name = fields.Char(string=_("Name"))
    company_id = fields.Many2one("res.company", string=_("Company"))
    wp_landing_page_id = fields.Integer(string=_("WP Landing Page"))
    status = fields.Selection(
        selection=[("draft", "Draft"), ("publish", "Publish")],
        default="draft",
        required=True,
        string=_("Status"),
    )
    allow_new_members = fields.Boolean(
        string=_("Allows new members"), related="company_id.allow_new_members"
    )
    number_of_members = fields.Integer(string=_("Number of members"))
    virtual_office_link = fields.Char(string=_("Virtual office link"))
    external_website_link = fields.Char(string=_("External website link"))
    # active_services = company_id.get_active_services()
    group_image_link = fields.Char(string=_("Group image link"))
    short_description = fields.Char(string=_("Short description"))
    long_description = fields.Text(string=_("Long description"))
    why_become_cooperator = fields.Text(string=_("Why become cooperator"))
    become_cooperator_process = fields.Text(string=_("Become cooperator process"))
    subscription_information = fields.Text(string=_("Subscription information"))
    new_cooperator_form_link = fields.Char(string=_("New cooperator form link"))
    contact_form = fields.Char(string=_("Contact form"))
    subscription_link = fields.Char(string=_("Subscription link"))
    social_media_link = fields.Char(string=_("Social media link"))
    map_geolocation = fields.Char(string=_("Map geolocation"))
    street = fields.Char(string=_("Street"))
    postal_code = fields.Char(string=_("Postal code"))
    city = fields.Char(string=_("City"))

    def to_dict(self):
        data = {
            "title": self.name,
            "odoo_company_id": self.company_id.id,
            "status": self.status,
            # "allow_new_members": self.allow_new_members,
            # "number_of_members": self.number_of_members,
            # "virtual_office_link": self.virtual_office_link,
            # "external_website_link": self.external_website_link,
            # # "active_services": self.active_services,
            # "group_image_link": self.group_image_link,
            # "short_description": self.short_description,
            # "long_description": self.long_description,
            # "why_become_cooperator": self.why_become_cooperator,
            # "become_cooperator_process": self.become_cooperator_process,
            # "subscription_information": self.subscription_information,
            # "new_cooperator_form_link": self.new_cooperator_form_link,
            # "contact_form": self.contact_form,
            # "subscription_link": self.subscription_link,
            # "social_media_link": self.social_media_link,
            # "map_geolocation": self.map_geolocation,
            # "street": self.street,
            # "postal_code": self.postal_code,
            # "city": self.city,
        }
        return data

    def action_landing_page_status(self):
        for record in self:
            new_status = "draft" if record.status == "publish" else "publish"

            username = self.company_id.wordpress_db_username # "odoo_rest_user"
            password = self.company_id.wordpress_db_password # "9SN6H8A@E87lxV)h"
            auth = Authenticate(username, password).authenticate()
            token = "Bearer %s" % auth["token"]
            landing_page_data = record.to_dict()
            landing_page_data["status"] = new_status
            landing_page_resource = LandingPageResource(record.wp_landing_page_id)
            landing_page_resource.update(token, landing_page_data)

            record.write({"status": new_status})
