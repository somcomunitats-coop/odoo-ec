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
                MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF["member_associations"]
            ).id: "member_associations",
            self.env.ref(
                MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF["invited"]
            ).id: "invited",
            self.env.ref(
                MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF["voluntary"]
            ).id: "voluntary",
        }

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

    activate_form_specific_products = fields.Boolean(
        string="Activate form specific products",
        help="If checked, a public link will be activated to provide a new web form that is uniquely and specifically linked to this product (with the 2 variants of person/company). This link can be freely shared to offer registrations that directly use this product: by sending the link by email to candidates, embedding it in external web pages, or adding additional custom buttons on the Community's own website to the Platform.",
    )

    product_external_id = fields.Char(
        string="External ID", compute="_compute_external_id", store=True
    )

    html_specific_products = fields.Html(
        string="Custom paragraph in specific form", translate=True
    )

    def url_individual_button(self):
        MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE = (
            self.get_mapping_product_category_id_subscription_mode()
        )
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        code_lang_default = (
            self.env.company.default_lang_id.code or self.env.user.lang or "es"
        )
        url_individual = f"{base_url}/{code_lang_default}/subscription/"
        if self.categ_id.id in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys():
            url_individual += f"{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[self.categ_id.id]}/{self.company_id.company_external_id}"
        return {
            "type": "ir.actions.act_url",
            "url": url_individual,
            "target": "new",
        }

    def url_company_button(self):
        MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE = (
            self.get_mapping_product_category_id_subscription_mode()
        )
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        code_lang_default = (
            self.env.company.default_lang_id.code or self.env.user.lang or "es"
        )
        url_company = f"{base_url}/{code_lang_default}/subscription/"
        if (
            self.categ_id.id in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys()
            and MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[self.categ_id.id]
            != "voluntary"
        ):
            url_company += f"company_{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[self.categ_id.id]}/{self.company_id.company_external_id}"
        elif self.categ_id.id in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys():
            url_company += f"{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[self.categ_id.id]}/{self.company_id.company_external_id}"
        return {
            "type": "ir.actions.act_url",
            "url": url_company,
            "target": "new",
        }

    def url_specific_individual_button(self):
        MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE = (
            self.get_mapping_product_category_id_subscription_mode()
        )
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        code_lang_default = (
            self.env.company.default_lang_id.code or self.env.user.lang or "es"
        )
        url_specific_individual = f"{base_url}/{code_lang_default}/subscription/"
        if self.categ_id.id in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys():
            url_specific_individual += f"{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[self.categ_id.id]}/{self.company_id.company_external_id}/{self.product_external_id}"
        return {
            "type": "ir.actions.act_url",
            "url": url_specific_individual,
            "target": "new",
        }

    def url_specific_company_button(self):
        MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE = (
            self.get_mapping_product_category_id_subscription_mode()
        )
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        code_lang_default = (
            self.env.company.default_lang_id.code or self.env.user.lang or "es"
        )
        url_specific_company = f"{base_url}/{code_lang_default}/subscription/"
        if (
            self.categ_id.id in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys()
            and MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[self.categ_id.id]
            != "voluntary"
        ):
            url_specific_company += f"company_{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[self.categ_id.id]}/{self.company_id.company_external_id}/{self.product_external_id}"
        elif self.categ_id.id in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys():
            url_specific_company += f"{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[self.categ_id.id]}/{self.company_id.company_external_id}/{self.product_external_id}"
        return {
            "type": "ir.actions.act_url",
            "url": url_specific_company,
            "target": "new",
        }

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
