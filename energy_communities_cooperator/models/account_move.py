from odoo import fields, models

from odoo.addons.energy_communities.utils import user_creator


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "user.currentcompany.mixin"]

    membership_id = fields.Many2one(
        "cooperative.membership", string="Related membership"
    )
    voluntary_share_interest_return_id = fields.Many2one(
        "voluntary.share.interest.return",
        string="Related voluntary share interest return",
        ondelete="cascade",
    )
    voluntary_share_total_contribution = fields.Float(string="Total contribution")

    def post_process_confirm_paid(self, effective_date):
        if not self.membership_id:
            self.set_cooperator_effective(effective_date)

    def set_cooperator_effective(self, effective_date):
        super().set_cooperator_effective(effective_date)
        cooperative_membership = self.partner_id.get_cooperative_membership(
            self.company_id
        )
        if cooperative_membership:
            self.write({"membership_id": cooperative_membership.id})

    # TODO: Should we maintain this method?
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
        # we call/inherit the standard coopetaror function here because
        # it will take care of use/select the per-company customized templates (if exist)
        # or the global 'cooperator' one. It applies to those 2 'certificate' templates:
        # "cooperator.email_template_share_increase" in case self.partner_id.member
        # "cooperator.email_template_certificate" in else case
        mail_template_obj = super().get_mail_template_certificate()

        if self.subscription_request.is_voluntary:
            mail_template_obj = self.env.ref(
                "energy_communities_cooperator.email_template_conditions_voluntary_share"
            )

        return mail_template_obj

    def create_user(self, partner):
        user_obj = self.env["res.users"]
        vat = partner.vat

        user = user_obj.search([("login", "=", vat)])
        if not user:
            user = user_obj.search([("login", "=", vat), ("active", "=", False)])
            if user:
                user.sudo().write({"active": True})

        role_id = self.env.ref("energy_communities.role_ce_member")
        action = "create_user"
        if partner.company_id.create_user_in_keycloak:
            action = "create_kc_user"
        with user_creator(self.env) as component:
            component.create_users_from_cooperator_partners(
                partners=partner, role_id=role_id, action=action, force_invite=False
            )
        return user
