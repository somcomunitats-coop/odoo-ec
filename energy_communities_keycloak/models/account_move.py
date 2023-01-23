from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    def create_user(self, partner):
        user_obj = self.env["res.users"]
        vat = partner.vat

        user = user_obj.search([("login", "=", vat)])
        if not user:
            user = user_obj.search([("login", "=", vat), ("active", "=", False)])
            if user:
                user.sudo().write({"active": True})
            else:
                user_values = {"partner_id": partner.id, "login": vat}
                user = user_obj.sudo()._signup_create_user(user_values)
                # We requiere the user to update the password in keycloak
                # user.sudo().with_context({"create_user": True}).action_reset_password()
        return user
