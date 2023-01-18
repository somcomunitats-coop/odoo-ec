from odoo import api, models, fields, _
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def create_user(self, partner):
        """Caution: we are full overriding this function in order to avoid the
        call to action_reset_password that will send an email to the user from odoo

        :return: (res.users) the new user
        """
        return partner.activate_partner_in_comunitat_energetica()