from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError

class SubscriptionRequest(models.Model):
    _inherit = 'subscription.request'

    gender = fields.Selection(selection_add=[("not_binary", "Not binary"),
                                             ("not_share", "I prefer to not share it")])

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
        required_fields =  super(SubscriptionRequest,self).get_required_field()
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
