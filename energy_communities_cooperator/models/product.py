import hashlib

from odoo import _, api, fields, models
from odoo.http import request
from odoo.tools import float_compare

from ..config import MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF

# Subscription requests in these states have not been validated or paid, so
# changing the linked contribution price does not rewrite a committed amount.
SHARE_PRICE_SAFE_REQUEST_STATES = ("draft", "cancelled")


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
            not in ["voluntary"]
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
            not in ["voluntary"]
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

    @api.model
    def get_company_share_type_selection(self, company, category_ids=None):
        """Share types of one energy community, for the cooperator type filter.

        ``default_code`` is the stored selection key. Codes are unique in the
        returned list because a selection cannot offer the same key twice.
        Archived contributions are excluded so the filter only offers types
        that can still be used.
        """
        domain = [
            ("is_share", "=", True),
            ("company_id", "=", company.id),
        ]
        if category_ids:
            domain.append(("categ_id", "in", list(category_ids)))
        shares = self.env["product.product"].sudo().search(domain)
        selection = []
        seen_codes = set()
        for share in shares:
            code = share.default_code
            if not code or code in seen_codes:
                continue
            seen_codes.add(code)
            selection.append((code, share.short_name or code))
        return selection

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        """Keep a duplicated contribution without a short name.

        The short name is mandatory on the form, so leaving it empty forces a
        new value instead of reusing the source contribution's name.
        """
        self.ensure_one()
        default = dict(default or {})
        if self.is_share:
            default.setdefault("short_name", False)
        return super().copy(default)

    @api.onchange("short_name")
    def _onchange_short_name(self):
        for product in self:
            warning = product._get_short_name_duplicate_warning()
            if warning:
                return warning

    def _get_short_name_duplicate_warning(self):
        """Warn when another contribution of the same community uses this name.

        The warning does not block the save. Archived matches are called out
        explicitly so they are not confused with a contribution still in use.
        """
        self.ensure_one()
        if not self.is_share or not self.short_name:
            return
        company = self.company_id or self.env.company
        domain = [
            ("short_name", "=", self.short_name),
            ("is_share", "=", True),
            ("company_id", "=", company.id),
        ]
        if self._origin:
            domain.append(("id", "!=", self._origin.id))
        duplicates = (
            self.env["product.template"].with_context(active_test=False).search(domain)
        )
        if not duplicates:
            return
        has_active = bool(duplicates.filtered("active"))
        has_archived = bool(duplicates.filtered(lambda product: not product.active))
        if has_active and has_archived:
            message = _(
                "The short name '%s' already exists, including on an archived "
                "contribution.",
                self.short_name,
            )
        elif has_archived:
            message = _(
                "The short name '%s' already exists on an archived contribution.",
                self.short_name,
            )
        else:
            message = _("The short name '%s' already exists.", self.short_name)
        return {"warning": {"title": _("Note:"), "message": message}}

    @api.onchange("list_price")
    def _onchange_list_price(self):
        for product in self:
            warning = product._get_share_list_price_change_warning()
            if warning:
                return warning

    def _get_share_list_price_change_warning(self):
        """Warn before changing the price of a contribution already in use.

        Only subscription requests outside draft and cancelled count. The
        warning does not block the save.
        """
        self.ensure_one()
        if not self.is_share or not self._origin:
            return
        precision = self.env["decimal.precision"].precision_get("Product Price")
        if (
            float_compare(
                self.list_price,
                self._origin.list_price,
                precision_digits=precision,
            )
            == 0
        ):
            return
        variant_ids = self._origin.product_variant_ids.ids
        if not variant_ids:
            return
        company = self.company_id or self.env.company
        linked_request = self.env["subscription.request"].search(
            [
                ("share_product_id", "in", variant_ids),
                ("company_id", "=", company.id),
                ("state", "not in", list(SHARE_PRICE_SAFE_REQUEST_STATES)),
            ],
            limit=1,
        )
        if not linked_request:
            return
        return {
            "warning": {
                "title": _("Note:"),
                "message": _(
                    "ATTENTION: There are already subscription requests linked to this "
                    "contribution that have been validated/paid using the preexisting price.\n"
                    "\n"
                    "We do not recommend changing this price, as doing so will automatically "
                    "recalculate/update the values of the fields that depend on this price "
                    "(linked contribution price and total requested amount) in the request "
                    "list view, including for requests that were already validated/paid under "
                    "the preexisting price.\n"
                    "\n"
                    "If the change responds to a formal decision by the energy community to "
                    "modify the price to be charged from now on for this contribution, we "
                    "recommend DUPLICATING the contribution and, in this way, generating a "
                    "NEW contribution that carries the new price and that will from now on "
                    "be linked to the forms and to new requests (if the preexisting "
                    "contribution should no longer be used, unlink it from the forms and "
                    "ARCHIVE it so that it is no longer available)."
                ),
            }
        }
