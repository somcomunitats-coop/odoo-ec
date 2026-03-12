from datetime import datetime

from odoo import api, fields, models
from odoo.tools.translate import _

from ..config import MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF


class CooperativeMembership(models.Model):
    _name = "cooperative.membership"
    _inherit = ["cooperative.membership", "user.currentcompany.mixin"]

    @api.depends(
        "partner_id.share_ids",
        "partner_id.share_ids.share_product_id",
        "partner_id.share_ids.share_product_id.categ_id",
        "partner_id.share_ids.share_product_id.categ_id.type_url",
    )
    def _compute_membership_type(self):
        # Get mapping directly to avoid dependency on type_url during initialization
        mapping = self.env[
            "product.category"
        ].get_mapping_product_category_id_subscription_mode()
        for record in self:
            membership_type = ""
            for line in record.share_ids:
                if line.share_number > 0:
                    categ_id = line.share_product_id.categ_id.id
                    # Use mapping if available, otherwise fallback to type_url
                    if mapping and categ_id in mapping:
                        membership_type = mapping[categ_id]
                    elif line.share_product_id.categ_id.type_url:
                        membership_type = line.share_product_id.categ_id.type_url
                    break
            record.membership_type = membership_type

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
    effective_invited = fields.Boolean(string="Effective Invited", default=False)
    membership_type = fields.Char(
        string="Membership Type",
        compute="_compute_membership_type",
        store=True,
        readonly=True,
    )

    @api.depends(
        "member", "effective_invited", "partner_id.subscription_request_ids.state"
    )
    def _compute_coop_candidate(self):
        for record in self:
            if record.member:
                is_candidate = False
            elif record.effective_invited:
                is_candidate = False
            else:
                sub_requests = record.subscription_request_ids.filtered(
                    lambda record: record.state == "done"
                )
                is_candidate = bool(sub_requests)

            record.coop_candidate = is_candidate

    coop_candidate = fields.Boolean(
        string="Cooperator candidate",
        compute=_compute_coop_candidate,
        store=True,
    )

    def _get_share_type(self):
        categ_ids = [
            self.env.ref(MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF["member"]).id,
            self.env.ref(MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF["invited"]).id,
            # self.env.ref(MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF["voluntary"]).id,
        ]
        shares = self.env["product.product"].search(
            [("is_share", "=", True), ("categ_id", "in", categ_ids)]
        )
        return [(s.default_code, s.short_name) for s in shares]

    def assign_cooperator_register_number(self):
        """Set a new cooperator register number on the memberships if one is not
        already assigned.
        If the membership type is invited, the cooperator register number is set to 0.
        """
        invited = self.filtered(
            lambda m: "invited"
            in m.subscription_request_ids.mapped("subscription_mode")
        )
        not_invited = self - invited
        for membership in invited:
            membership.cooperator_register_number = 0
        if not_invited:
            super(
                CooperativeMembership, not_invited
            ).assign_cooperator_register_number()

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
