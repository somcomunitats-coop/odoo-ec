import hashlib

from odoo import api, fields, models
from odoo.http import request


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.depends("company_id")
    def _compute_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for record in self:
            record.url_individual = f"{base_url}/subscription/member/{record.company_id.company_external_id}"
            record.url_company = f"{base_url}/subscription/company_memeber/{record.company_id.company_external_id}"

    @api.depends("company_id", "product_external_id")
    def _compute_url_specific(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for record in self:
            record.url_specific_individual = f"{base_url}/subscription/member/{record.company_id.company_external_id}/{record.product_external_id}"
            record.url_specific_company = f"{base_url}/subscription/company_member/{record.company_id.company_external_id}/{record.product_external_id}"

    @api.depends("name")
    def _compute_external_id(self):
        for record in self:
            record.product_external_id = hashlib.sha1(
                str(record.id).encode()
            ).hexdigest()

    mail_template = fields.Many2one(
        comodel_name="mail.template",
        string="Certificate email template",
        domain=[("model", "=", "res.partner")],
        help="If left empty, the default global mail template will be used.",
    )
    url_individual = fields.Char(
        String="URL individual", compute="_compute_url", readonly=True
    )
    url_company = fields.Char(
        String="URL company", compute="_compute_url", readonly=True
    )

    activate_form_specific_products = fields.Boolean(
        string="Activate form specific products"
    )

    url_specific_individual = fields.Char(
        String="URL individual", compute="_compute_url_specific", readonly=True
    )
    url_specific_company = fields.Char(
        String="URL company", compute="_compute_url_specific", readonly=True
    )
    product_external_id = fields.Char(
        string="External ID", compute="_compute_external_id", store=True
    )

    html_specific_products = fields.Html(
        string="Custom paragraph in specific form", translate=True
    )

    # TODO: This must be interated on new coopeator version
    def get_web_share_products(self, is_company):
        """We are fully overriding this function in order to make it multi-company sensitive"""

        if request:
            default_company = request.env["res.company"].browse(
                request.env.context.get("target_odoo_company_id")
            )
        else:
            default_company = self.env.user_id.company_id

        target_company = default_company

        if (
            self.env.context.get("target_odoo_company_id", False)
            and self.env.context.get("target_odoo_company_id") != default_company.id
        ):
            target_company = self.env["res.company"].browse(
                self.env.context.get("target_odoo_company_id")
            )

        if is_company is True:
            product_templates = self.env["product.template"].search(
                [
                    ("is_share", "=", True),
                    ("display_on_website", "=", True),
                    ("by_company", "=", True),
                    ("company_id", "=", target_company.id),
                ]
            )
        else:
            product_templates = self.env["product.template"].search(
                [
                    ("is_share", "=", True),
                    ("display_on_website", "=", True),
                    ("by_individual", "=", True),
                    ("company_id", "=", target_company.id),
                ]
            )
        return product_templates
