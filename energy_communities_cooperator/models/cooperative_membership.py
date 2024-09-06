from datetime import datetime

from odoo import api, fields, models
from odoo.tools.translate import _


class CooperativeMembership(models.Model):
    _name = "cooperative.membership"
    _inherit = ["cooperative.membership", "user.currentcompany.mixin"]

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
    partner_phone = fields.Char(related="partner_id.phone", store=True)
    partner_email = fields.Char(related="partner_id.email", store=True)
    partner_vat = fields.Char(related="partner_id.vat", store=True)

    @api.depends("subscription_request_ids")
    def _compute_subscription_invoice_ids(self):
        for record in self:
            invs = []
            for subs in record.subscription_request_ids:
                for invoice in subs.capital_release_request:
                    invs.append((4, invoice.id))
            if invs:
                record.subscription_invoice_ids = invs
            else:
                record.subscription_invoice_ids = False

    def action_create_share_line_wizard(self):
        self.ensure_one()
        share_line_form_view = self.env.ref(
            "energy_communities_cooperator.share_line_form", False
        )
        return {
            "name": _("Create a share line"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "share.line",
            "view_id": share_line_form_view.id,
            "target": "new",
            "context": {
                "default_partner_id": self.partner_id.id,
                "default_effective_date": datetime.now(),
            },
        }
