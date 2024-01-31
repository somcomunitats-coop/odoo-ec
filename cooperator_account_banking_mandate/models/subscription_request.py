from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SubscriptionRequest(models.Model):
    _inherit = "subscription.request"

    mandate_id = fields.Many2one(
        "account.banking.mandate",
        string="Direct Debit Mandate",
        ondelete="restrict",
        check_company=True,
        readonly=False,
        domain="[('state', 'in', ('draft', 'valid')), ('partner_id', '=', partner_id)]",
    )
    mandate_required = fields.Boolean(
        related="payment_mode_id.payment_method_id.mandate_required",
    )
    mandate_approved = fields.Boolean(
        required=True, default=False, string="Approved creation of new mandate"
    )

    def create_invoice(self, partner):
        if self.mandate_required and not self.mandate_id:
            self.mandate_id = self.create_mandate()
        return super().create_invoice(partner)

    def create_mandate(self):
        if not self.partner_id:
            raise ValidationError(_("Must assign a valid cooperator."))
        if not self.mandate_approved:
            raise ValidationError(_("Must check the mandate creation."))
        return self.env["account.banking.mandate"].create(self.get_mandate_values())

    def get_invoice_vals(self, partner):
        vals = super().get_invoice_vals(partner)
        vals["mandate_id"] = self.mandate_id.id
        return vals

    def get_bank(self):
        if not self.iban:
            raise ValidationError(_("Must assign a valid iban."))
        bank_id = self.partner_id.bank_ids.filtered(lambda x: x.acc_number)
        # TODO normalize iban
        if bank_id:
            return bank_id
        return self.env["res.partner.bank"].create(
            {
                "partner_id": self.partner_id.id,
                "acc_number": self.iban,
            }
        )

    def get_mandate_values(self):
        bank_id = self.get_bank()
        return {
            "format": "sepa",
            "type": "recurrent",
            "state": "valid",
            "signature_date": self.date,
            "partner_bank_id": bank_id.id,
            "partner_id": self.partner_id.id,
            "company_id": self.company_id.id,
        }

    @api.onchange("partner_id")
    def onchange_partner(self):
        super().onchange_partner()
        self.mandate_id = False
