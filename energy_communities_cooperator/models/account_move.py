from odoo import _, api, fields, models


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
            self.company_id.id
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
        if self.subscription_request.is_voluntary:
            mail_template = "energy_communities_cooperator.email_template_conditions_voluntary_share"
        elif self.partner_id.member:
            mail_template = "cooperator.email_template_certificat_increase"
        else:
            mail_template = "cooperator.email_template_certificat"
        return self.env.ref(mail_template)
