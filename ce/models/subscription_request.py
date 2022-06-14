from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError

class SubscriptionRequest(models.Model):
    _inherit = 'subscription.request'

    def get_journal(self):
        """Need to override in order to use in multicompany enviroment"""

        j = super().get_journal()

        if self.company_id.id != 1:
            if self.company_id.cooperator_journal:
                j = self.company_id.cooperator_journal
            else:
                raise UserError(_("You must set a cooperator journal on you company."))

        return j



