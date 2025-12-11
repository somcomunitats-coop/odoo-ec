from odoo import fields, models

from ..config import MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF


class ProductCategory(models.Model):
    _inherit = "product.category"

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

    def _compute_share_urls(self):
        MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE = (
            self.get_mapping_product_category_id_subscription_mode()
        )
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        code_lang_default = (
            self.env.company.default_lang_id.code or self.env.user.lang.code or "es"
        )
        for record in self:
            if record.id in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys():
                record.type_url = MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[
                    record.id
                ]
                record.url_individual = f"{base_url}/{code_lang_default}/subscription/{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[record.id]}/{self.env.company.company_external_id}"
                if (
                    MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[record.id]
                    != "voluntary"
                ):
                    record.url_company = f"{base_url}/{code_lang_default}/subscription/company_{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[record.id]}/{self.env.company.company_external_id}"
                else:
                    record.url_company = None
            else:
                record.url_individual = None
                record.url_company = None
                record.type_url = None

    type_url = fields.Char(
        string="Type URL",
        compute="_compute_share_urls",
        readonly=True,
    )
    url_individual = fields.Char(
        string="URL individual",
        compute="_compute_share_urls",
        readonly=True,
    )
    url_company = fields.Char(
        string="URL company",
        compute="_compute_share_urls",
        readonly=True,
    )
