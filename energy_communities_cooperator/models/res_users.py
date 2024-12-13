from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _name = "res.users"
    _inherit = "res.users"

    # Bypass, cooperator try to create user 'login' based on email but against our VAT policy for the login
    @api.model
    def _signup_create_user(self, values):
        if "partner_id" in values.keys():
            rel_partner = self.env["res.partner"].browse(values["partner_id"])
            if rel_partner.vat:
                values["login"] = rel_partner.vat
                existing_user = self.env["res.users"].search(
                    [("login", "=", values["login"])]
                )
                if existing_user:
                    raise ValidationError(
                        _(
                            "Trying to create user from partner ID {partner_id} but user ID {user_id} is using the vat. Contact your system administrator if you have questions."
                        ).format(partner_id=rel_partner.id, user_id=existing_user[0].id)
                    )
            else:
                raise ValidationError(
                    _(
                        "Trying to create user from partner ID {} but the partner doesn't have VAT defined"
                    ).format(rel_partner.id)
                )
        return super()._signup_create_user(values)
