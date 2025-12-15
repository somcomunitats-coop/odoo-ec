from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..config import MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF


class SubscriptionRequest(models.Model):
    _name = "subscription.request"
    _inherit = "subscription.request"
    _description = "Subscription request"

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

    @api.depends("share_product_id", "share_product_id.categ_id")
    def _compute_subscription_mode(self):
        MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE = (
            self.get_mapping_product_category_id_subscription_mode()
        )
        for record in self:
            if (
                record.share_product_id.categ_id.id
                in MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE.keys()
            ):
                record.subscription_mode = MAPPING__PRODUCT_CATEG_ID__SUBSCRIPTION_MODE[
                    record.share_product_id.categ_id.id
                ]
            else:
                record.subscription_mode = "generic"

    def get_subscription_mode_selection(self):
        return [
            ("generic", "Generic"),
            ("member", "Member"),
            ("invited", "Invited"),
            ("voluntary", "Voluntary"),
        ]

    gender = fields.Selection(
        selection_add=[
            ("not_binary", "Not binary"),
            ("not_share", "I prefer to not share it"),
        ]
    )
    vat = fields.Char(
        required=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    subscription_mode = fields.Selection(
        string="Subscription mode",
        selection=lambda self: self.get_subscription_mode_selection(),
        compute="_compute_subscription_mode",
        default="generic",
        store=True,
        readonly=True,
    )
    share_product_categ_id = fields.Many2one(
        "product.category",
        string="Share type category",
        compute="_compute_share_product_categ_id",
        store=True,
    )

    @api.depends("share_product_id")
    def _compute_share_product_categ_id(self):
        for record in self:
            record.share_product_categ_id = False
            if record.share_product_id.categ_id:
                record.share_product_categ_id = record.share_product_id.categ_id.id

    def compute_share_product_categ_id(self):
        self._compute_share_product_categ_id()
        return True

    @api.onchange("partner_id")
    def onchange_partner(self):
        self.ensure_one()
        super().onchange_partner()
        if self.partner_id.vat:
            self.vat = self.partner_id.vat

    def get_required_field(self):
        required_fields = super().get_required_field()
        if "iban" in required_fields:
            required_fields.remove("iban")
        return required_fields

    @api.model_create_multi
    def create(self, vals):
        # Somewhere the company_id is assigned as string
        # Can't find where, this is a workaround
        for val in vals:
            if "company_id" in val:
                val["company_id"] = int(val["company_id"])
            if "country_id" in val:
                val["country_id"] = int(val["country_id"])
            # setup company_register_number on SR based on vat
            if "vat" in val.keys():
                val["company_register_number"] = val["vat"]

        subscription_request = super().create(vals)
        if (
            not subscription_request.payment_mode_id.payment_method_id.code
            == "sepa_direct_debit"
        ):
            subscription_request.skip_iban_control = True
        return subscription_request

    def validate_subscription_request(self):
        if self.subscription_mode == "voluntary" and not self.partner_id:
            raise ValidationError(
                _(
                    "You can't create a voluntary subscription share for a new cooperator."
                )
            )
        if self.subscription_mode != "voluntary" and self.type == "new" and self.vat:
            partners = self.env["res.partner"].search([("vat", "ilike", self.vat)])
            if partners:
                partner = partners[0]
                membership = partner._get_member_or_candidate_cooperative_membership(
                    self.company_id.id
                )
                if membership:
                    raise ValidationError(
                        _(
                            "There is an existing account for this"
                            " vat number on this community. "
                        )
                    )
        super().validate_subscription_request()

    def get_partner_vals(self):
        vals = super().get_partner_vals()
        # vals["company_id"] = self.company_id.id
        return vals

    def get_partner_company_vals(self):
        vals = super().get_partner_company_vals()
        # vals["company_id"] = self.company_id.id
        # This propagates vat from SR to res.partner
        vals["vat"] = self.vat
        return vals

    def get_representative_vals(self):
        vals = super().get_representative_vals()
        # vals["company_id"] = self.company_id.id
        return vals

    def _find_partner_from_create_vals(self, vals):
        # we don't stablish related partner on SR from cooperator website or creating manually
        # On voluntary shares partner searched on controller
        if vals["source"] not in ["website", "manual"]:
            partner_model = self.env["res.partner"]
            partner_id = vals.get("partner_id")
            if partner_id:
                return partner_model.browse(partner_id)
            if vals.get("is_company"):
                partner = partner_model.sudo().get_cooperator_from_crn(
                    vals.get("company_register_number")
                )
            else:
                partner = partner_model.sudo().get_cooperator_from_vat(vals.get("vat"))
            if partner:
                vals["partner_id"] = partner.id
        else:
            partner = False
        return partner

    def _get_partner_domain(self):
        # used for representative
        if self.is_company:
            if self.email:
                return [("email", "=", self.email), ("is_company", "=", False)]
            else:
                return None
        # used for members (normal and company)
        else:
            if self.vat:
                return [("vat", "=", self.vat)]
            else:
                return None

    def _find_or_create_partner(self):
        if self.subscription_mode == "voluntary":
            super_model = super()
        else:
            super_model = super(SubscriptionRequest, self.sudo())
        related_partner = super_model._find_or_create_partner()
        if self.company_id.id not in related_partner.company_ids.mapped("id"):
            related_partner.write({"company_ids": [(4, self.company_id.id)]})
        return related_partner

    def create_coop_partner(self):
        partner_obj = self.env["res.partner"]
        if self.is_company:
            partner_vals = self.get_partner_company_vals()
        else:
            partner_vals = self.get_partner_vals()
        partner = partner_obj.create(partner_vals)
        return partner

    def _find_or_create_representative(self):
        super(SubscriptionRequest, self.sudo())._find_or_create_representative()

    def set_membership(self):
        if self.is_company:
            partner = self._find_or_create_partner()
            representative = partner.get_representative()
            rep_membership = self.env["cooperative.membership"].search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("partner_id", "=", representative.id),
                    ("representative", "=", True),
                ]
            )
            if not rep_membership:
                representative.create_cooperative_membership(self.company_id.id)
        # To be overridden
        return True

    # TODO: This method has been overwritten from cooperator. Find a better solution for this
    def _send_confirmation_mail(self):
        if self.company_id.send_confirmation_email and not self.is_operation:
            mail_template_notif = (
                self.company_id.get_cooperator_confirmation_mail_template()
            )
            if self.subscription_mode == "voluntary":
                mail_template_notif = self.env.ref(
                    "energy_communities_cooperator.email_template_confirmation_voluntary_share"
                )
            # sudo is needed to change state of invoice linked to a request
            #  sent through the api
            mail_template_notif.sudo().send_mail(
                force_send=False,
                res_id=self.id,
                email_layout_xmlid="mail.mail_notification_layout",
            )

    def validate_subscription_request_with_company(self):
        """
        This method is used in data demo importation to be able to validate with the context of the company instead of
        the main company in the installation of the module.
        :return:
        """
        self = self.with_company(self.company_id)
        self.validate_subscription_request()
        return True

    def _prepare_invoice_line(self, move_id, product, partner, qty):
        res = super()._prepare_invoice_line(move_id, product, partner, qty)
        res["tax_ids"] = product.taxes_id
        return res
