from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # cooperative_membership_id = fields.Many2one(
    #     "cooperative.membership",
    #     "Cooperative Membership For Current Company",
    #     compute="_compute_cooperative_membership_id",
    #     store=False,
    # )
    # cooperative_membership_id = fields.Many2one(
    #     "cooperative.membership",
    #     "Cooperative Membership For Current Company",
    #     compute="_compute_cooperative_membership_id",
    #     store=False,
    # )

    def compute_cooperative_membership_id(self):
        self._compute_cooperative_membership_id()
        return True

    # @api.depends("cooperative_membership_ids")
    # def _compute_cooperative_membership_id(self):
    #     for record in self:
    #         rel_membership = record.cooperative_membership_ids.filtered(lambda membership: membership.company_id.id == self.env.company.id)
    #         if rel_membership:
    #             record.cooperative_membership_id = rel_membership.id
    #         else:
    #             record.cooperative_membership_id = False
