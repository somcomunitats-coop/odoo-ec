from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    def create_user(self, partner):
        user_obj = self.env["res.users"]
        vat = partner.vat

        user = user_obj.search([("login", "=", vat)])
        if not user:
            user = user_obj.search([("login", "=", vat), ("active", "=", False)])
            if user:
                user.sudo().write({"active": True})
            else:
                user_values = {
                    "partner_id": partner.id,
                    "login": vat,
                    "company_ids": [partner.company_id.id],
                    "company_id": partner.company_id.id,
                    "role_line_ids": [
                        (
                            0,
                            0,
                            {
                                "role_id": self.env.ref(
                                    "energy_communities.role_ce_member"
                                ).id,
                                "company_id": partner.company_id.id,
                            },
                        )
                    ],
                }
                user = user_obj.sudo()._signup_create_user(user_values)
                # We requiere the user to update the password in keycloak
                # user.sudo().with_context({"create_user": True}).action_reset_password()
                if partner.company_id.create_user_in_keycloak:
                    user.create_users_on_keycloak()
        return user

    def send_capital_release_request_mail(self):
        # temporal fix por Gares Bide needs
        # capital_release_mail only must be sent when is a mandatory share
        # TODO Remove it and implement a configuration
        if not self.subscription_request.is_voluntary:
            return super().send_capital_release_request_mail()

    def _get_starting_sequence(self):
        self.ensure_one()
        if not self.release_capital_request:
            return super()._get_starting_sequence()
        starting_sequence = "%s/%04d/000" % (self.journal_id.code, self.date.year)
        if self.journal_id.refund_sequence and self.move_type in (
            "out_refund",
            "in_refund",
        ):
            starting_sequence = "R" + starting_sequence
        return starting_sequence

    def get_mail_template_certificate(self):
        if self.subscription_request.is_voluntary:
            mail_template = (
                "energy_communities.email_template_conditions_voluntary_share"
            )
        elif self.partner_id.member:
            mail_template = "cooperator.email_template_certificat_increase"
        else:
            mail_template = "cooperator.email_template_certificat"
        return self.env.ref(mail_template)
