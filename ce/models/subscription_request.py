from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError

class SubscriptionRequest(models.Model):
    _inherit = 'subscription.request'

    gender = fields.Selection(
        [("male", _("Male")), ("female", _("Female")), ("not_binary", _("Not binary")),
        ("not_share", _("I prefer to not share it")), ("other", _("Other"))],
        string="Gender",
        readonly=True,
        states={"draft": [("readonly", False)]},
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
        required_fields =  super(SubscriptionRequest,self).get_required_field()
        if 'iban' in required_fields: required_fields.remove('iban')
        return required_fields

    @api.model
    def create(self, vals):
        if vals:
            vals['skip_iban_control'] = True
        subscription_request = super(SubscriptionRequest, self).create(vals)
        return subscription_request
