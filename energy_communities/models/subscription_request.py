from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class SubscriptionRequest(models.Model):
    _inherit = 'subscription.request'

    gender = fields.Selection(selection_add=[("not_binary", "Not binary"),
                                             ("not_share", "I prefer to not share it")])
    vat = fields.Char(required=True, readonly=True, states={"draft": [("readonly", False)]})

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
        required_fields = super(SubscriptionRequest, self).get_required_field()
        if 'iban' in required_fields: required_fields.remove('iban')
        return required_fields

    @api.model
    def create(self, vals):
        if vals:
            vals['skip_iban_control'] = True

        # Somewhere the company_id is assigned as string
        # Can't find where, this is a workaround
        if 'company_id' in vals:
            vals['company_id'] = int(vals['company_id'])
        if 'country_id' in vals:
            vals['country_id'] = int(vals['country_id'])
        subscription_request = super(SubscriptionRequest, self).create(vals)
        return subscription_request

    def get_partner_vals(self):
        vals = super(SubscriptionRequest, self).get_partner_vals()
        vals["company_id"] = self.company_id.id
        return vals

    def get_partner_company_vals(self):
        vals = super(SubscriptionRequest, self).get_partner_company_vals()
        vals["company_id"] = self.company_id.id
        return vals

    def get_representative_vals(self):
        vals = super(SubscriptionRequest, self).get_representative_vals()
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
        if is_company:
            mail_template = "energy_communities.email_template_confirmation_company"
        else:
            mail_template = "cooperator.email_template_confirmation"
        return self.env.ref(mail_template, False)