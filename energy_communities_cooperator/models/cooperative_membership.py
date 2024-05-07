from odoo import api, fields, models


class CooperativeMembership(models.Model):
    _name = "cooperative.membership"
    _inherit = ["cooperative.membership"]
    # _inherit = ["cooperative.membership","user.currentcompany.mixin"]

    active = fields.Boolean(string="Active", default=True)
    representative = fields.Boolean(
        string="Legal Representative", related="partner_id.representative", store=True
    )
    representative_of_member_company = fields.Boolean(
        string="Company Legal Representative",
        related="partner_id.representative_of_member_company",
        store=False,
    )
    subscription_invoice_ids = fields.One2many(
        "account.move",
        string="Subscription invoices",
        compute="_compute_subscription_invoice_ids",
        store=False,
    )
    partner_id = fields.Many2one(
        "res.partner",
        "Partner",
        required=True,
        readonly=False,
        ondelete=None,
        index=False,
    )

    @api.depends("subscription_request_ids")
    def _compute_subscription_invoice_ids(self):
        for record in self:
            invs = []
            for subs in record.subscription_request_ids:
                for invoice in subs.capital_release_request:
                    invs.append((4, invoice.id))
            print(invs)
            if invs:
                record.subscription_invoice_ids = invs
            else:
                record.subscription_invoice_ids = False
