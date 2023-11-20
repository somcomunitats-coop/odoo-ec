from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SubscriptionRequest(models.Model):
    _inherit = "subscription.request"

    @api.depends("share_product_id", "share_product_id.categ_id")
    def _compute_is_voluntary(self):
        product_category_voluntary_share = self.env.ref(
            "energy_communities.product_category_company_voluntary_share",
            raise_if_not_found=False,
        )
        for record in self:
            record.is_voluntary = (
                record.share_product_id.categ_id == product_category_voluntary_share
            )

    gender = fields.Selection(
        selection_add=[
            ("not_binary", "Not binary"),
            ("not_share", "I prefer to not share it"),
        ]
    )
    vat = fields.Char(
        required=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    is_voluntary = fields.Boolean(
        compute=_compute_is_voluntary,
        string="Is voluntary contribution",
        readonly=True,
        store=True,
    )

    def get_journal(self):
        """Need to override in order to use in multicompany enviroment"""

        j = super().get_journal()

        if self.company_id.id != 1:
            if self.company_id.cooperator_journal:
                j = self.company_id.cooperator_journal
            else:
                raise UserError(_("You must set a cooperator journal on you company."))

        return j

    def get_required_field(self):
        required_fields = super().get_required_field()
        if "iban" in required_fields:
            required_fields.remove("iban")
        return required_fields

    @api.model
    def create(self, vals):
        # Somewhere the company_id is assigned as string
        # Can't find where, this is a workaround
        if "company_id" in vals:
            vals["company_id"] = int(vals["company_id"])
        if "country_id" in vals:
            vals["country_id"] = int(vals["country_id"])
        subscription_request = super().create(vals)
        if (
            not subscription_request.payment_mode_id.payment_method_id.code
            == "sepa_direct_debit"
        ):
            subscription_request.skip_iban_control = True
        return subscription_request

    def validate_subscription_request(self):
        if self.is_voluntary and self.type == "new":
            raise ValidationError(
                _(
                    "You can't create a voluntary subscription share for a new cooperator."
                )
            )
        super().validate_subscription_request()

    def get_partner_vals(self):
        vals = super().get_partner_vals()
        vals["company_id"] = self.company_id.id
        return vals

    def get_partner_company_vals(self):
        vals = super().get_partner_company_vals()
        vals["company_id"] = self.company_id.id
        return vals

    def get_representative_vals(self):
        vals = super().get_representative_vals()
        vals["company_id"] = self.company_id.id
        return vals

    def _find_partner_from_create_vals(self, vals):
        partner_model = self.env["res.partner"]
        partner_id = vals.get("partner_id")
        if partner_id:
            return partner_model.browse(partner_id)
        if vals.get("is_company"):
            partner = partner_model.get_cooperator_from_crn(
                vals.get("company_register_number")
            )
        else:
            partner = partner_model.get_cooperator_from_vat(vals.get("vat"))
        if partner:
            vals["partner_id"] = partner.id
        return partner

    def get_mail_template_notif(self, is_company=False):
        if self.is_voluntary:
            mail_template = (
                "energy_communities.email_template_confirmation_voluntary_share"
            )
        else:
            if is_company:
                mail_template = "energy_communities.email_template_confirmation_company"
            else:
                mail_template = "cooperator.email_template_confirmation"
        return self.env.ref(mail_template, False)

    def _send_confirmation_mail(self):
        if self.company_id.send_confirmation_email:
            if self.is_voluntary and not self.partner_id:
                return False
            mail_template_notif = self.get_mail_template_notif(
                is_company=self.is_company
            )
            # sudo is needed to change state of invoice linked to a request
            #  sent through the api
            mail_template_notif.sudo().send_mail(self.id)

    def validate_subscription_request_with_company(self):
        """
        This method is used in data demo importation to be able to validate with the context of the company instead of
        the main company in the installation of the module.
        :return:
        """
        self = self.with_company(self.company_id)
        return self.validate_subscription_request()

    def _prepare_invoice_line(self, product, partner, qty):
        res = super()._prepare_invoice_line(product, partner, qty)
        res["tax_ids"] = product.taxes_id

        return res
