from odoo import fields, models

from ..config import MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF


class ProductCategory(models.Model):
    _inherit = "product.category"

    def get_mapping_product_category_id_subscription_mode(self):
        mapping = {}
        for mode, xmlid in MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF.items():
            if mode in ("member", "invited", "voluntary", "member_associations"):
                try:
                    category = self.env.ref(xmlid, raise_if_not_found=False)
                    if category:
                        mapping[category.id] = mode
                except ValueError:
                    # XML ID not yet loaded during module initialization
                    pass
        return mapping

    def _compute_type_url(self):
        MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE = (
            self.get_mapping_product_category_id_subscription_mode()
        )
        # If mapping is empty (during module initialization), set all to None
        # This will be recalculated once XML data is loaded
        if not MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE:
            for record in self:
                record.type_url = None
            return
        for record in self:
            if record.id in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys():
                record.type_url = MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[
                    record.id
                ]
            else:
                record.type_url = None

    type_url = fields.Char(
        string="Type URL",
        compute="_compute_type_url",
        readonly=True,
    )
    product_website = fields.Boolean(
        string="Product Website",
        default=False,
        company_dependent=True,
        help="If checked, the group of fields in the generic form will be hidden so that you can choose the product from the list of those included. The product that will be linked to the form by default will be the one marked in the ‘Default product in the generic form’ field.",
    )
    product_qty_must_be_read_only = fields.Boolean(
        string="Product Qty Must Be Read Only",
        default=False,
        company_dependent=True,
        help="If checked, the generic and specific web forms for products in this category are configured to allow the product quantity field to the right of the drop-down menu for selecting the product to be modified.",
    )
    share_form_header_text = fields.Html(
        string="Customizable paragraph in the header text of the form", translate=True
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
        if self.id in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys():
            url_individual += f"{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[self.id]}/{self.env.company.company_external_id}"
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
            self.id in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys()
            and MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[self.id] != "voluntary"
        ):
            url_company += f"company_{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[self.id]}/{self.env.company.company_external_id}"
        elif self.id in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys():
            url_company += f"{MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[self.id]}/{self.env.company.company_external_id}"
        return {
            "type": "ir.actions.act_url",
            "url": url_company,
            "target": "new",
        }
