import hashlib

from odoo import api, fields, models
from odoo.http import request

from ..config import MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_mapping_product_category_id_subscription_mode(self):
        return {
            self.env.ref(
                MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF["member"]
            ).id: "member",
            self.env.ref(
                MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF["invited"]
            ).id: "invited",
            self.env.ref(
                MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF["voluntary"]
            ).id: "voluntary",
        }

    @api.depends("company_id", "categ_id")
    def _compute_url(self):
        MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE = (
            self.get_mapping_product_category_id_subscription_mode()
        )
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for record in self:
            if (
                record.categ_id.id
                in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys()
            ):
                record.url_individual = f"{base_url}/subscription/{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[record.categ_id.id]}/{record.company_id.company_external_id}"
                if (
                    MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[record.categ_id.id]
                    != "voluntary"
                ):
                    record.url_company = f"{base_url}/subscription/company_{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[record.categ_id.id]}/{record.company_id.company_external_id}"
                else:
                    record.url_company = None
            else:
                record.url_individual = None
                record.url_company = None

    @api.depends("company_id", "product_external_id", "categ_id")
    def _compute_url_specific(self):
        MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE = (
            self.get_mapping_product_category_id_subscription_mode()
        )
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for record in self:
            if (
                record.categ_id.id
                in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys()
            ):
                record.url_specific_individual = f"{base_url}/subscription/{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[record.categ_id.id]}/{record.company_id.company_external_id}/{record.product_external_id}"
                if (
                    MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[record.categ_id.id]
                    != "voluntary"
                ):
                    record.url_specific_company = f"{base_url}/subscription/company_{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[record.categ_id.id]}/{record.company_id.company_external_id}/{record.product_external_id}"
                else:
                    record.url_specific_company = None
            else:
                record.url_specific_individual = None
                record.url_specific_company = None

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
