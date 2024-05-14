from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    membership_id = fields.Many2one(
        "cooperative.membership", string="Related membership"
    )

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
