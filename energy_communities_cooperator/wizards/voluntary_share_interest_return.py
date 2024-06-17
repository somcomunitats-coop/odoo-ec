from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class VoluntaryShareInterestReturn(models.TransientModel):
    _name = "voluntary.share.interest.return.wizard"
    _description = "Calculate and prepare interests to be returned in voluntary shares"

    interest = fields.Float(string="Interest")

    def execute_return(self):
        if "active_ids" in self.env.context.keys():
            impacted_companies = self.env["res.company"].browse(
                self.env.context["active_ids"]
            )
            for company in impacted_companies:
                self._consistency_validation(company)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "success",
                    "title": _("Interest generation successful"),
                    "message": _(
                        "We have calculated and generated the moves to pay voluntary share interest for this company."
                    ),
                    "sticky": False,
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }

    def _consistency_validation(self, company):
        voluntary_share_product = company.voluntary_share_id
        # check if all shares comes from an invoice
        memberships = self.env["cooperative.membership"].search(
            [("company_id", "=", company.id)]
        )
        for membership in memberships:
            total_in_membership = 0
            total_in_account_move = 0
            membership_voluntary_shares = membership.share_ids.filtered(
                lambda share_line: share_line.share_product_id.id
                == voluntary_share_product.id
            )
            for membership_voluntary_share in membership_voluntary_shares:
                total_in_membership += membership_voluntary_share.total_amount_line
                related_invoice_line = self._find_related_invoice_line_from_share_line(
                    membership_voluntary_share
                )
                if not related_invoice_line:
                    raise ValidationError(
                        _(
                            "ERROR on Membership {membership_id}. No related invoice line for voluntary share {share_id}".format(
                                membership_id=membership.id,
                                share_id=membership_voluntary_share.id,
                            )
                        )
                    )
                if len(related_invoice_line) > 1:
                    raise ValidationError(
                        _(
                            "ERROR on Membership {membership_id}. More than one related invoice line for voluntary share {share_id}".format(
                                membership_id=membership.id,
                                share_id=membership_voluntary_share.id,
                            )
                        )
                    )
            if total_in_membership > 0:
                related_membership_invoices = self.env["account.move"].search(
                    [
                        ("membership_id", "=", membership.id),
                        ("payment_state", "=", "paid"),
                    ]
                )
                if not related_membership_invoices:
                    raise ValidationError(
                        _(
                            "ERROR on Membership {}. No related invoice for voluntary share".format(
                                membership.id
                            )
                        )
                    )
                else:
                    for membership_invoice in related_membership_invoices:
                        for line in membership_invoice.invoice_line_ids.filtered(
                            lambda invoice_line: invoice_line.product_id.id
                            == voluntary_share_product.id
                        ):
                            total_in_account_move += line.price_subtotal
                    if total_in_membership != total_in_account_move:
                        raise ValidationError(
                            "ERROR on Membership {}. Invoice total not matching share lines".format(
                                membership.id
                            )
                        )
        # Check if total in voluntary share invoices match share lines
        company_invoices_partners = (
            self.env["account.move"]
            .search([("company_id", "=", company.id), ("payment_state", "=", "paid")])
            .mapped("partner_id")
        )
        for partner in company_invoices_partners:
            if partner.cooperator:
                total_in_account_move = 0
                total_in_membership = 0
                partner_company_invoices = self.env["account.move"].search(
                    [
                        ("company_id", "=", company.id),
                        ("payment_state", "=", "paid"),
                        ("partner_id", "=", partner.id),
                    ]
                )
                for line in partner_company_invoices.invoice_line_ids.filtered(
                    lambda invoice_line: invoice_line.product_id.id
                    == voluntary_share_product.id
                ):
                    if not line.move_id.membership_id:
                        raise ValidationError(
                            _(
                                "ERROR on Invoice {}. No related membership defined".format(
                                    line.move_id.id
                                )
                            )
                        )
                    else:
                        if line.move_id.membership_id.company_id != company.id:
                            raise ValidationError(
                                _(
                                    "ERROR on Invoice {}. Related membership not in same company".format(
                                        line.move_id.id
                                    )
                                )
                            )
                    total_in_account_move += line.price_subtotal
                related_partner_membership = self.env["cooperative.membership"].search(
                    [("company_id", "=", company.id), ("partner_id", "=", partner.id)]
                )
                if not related_partner_membership:
                    raise ValidationError(
                        _(
                            "ERROR on partner {}. Related membership not found".format(
                                partner.id
                            )
                        )
                    )
                if len(related_partner_membership) > 1:
                    raise ValidationError(
                        _(
                            "ERROR on partner {}. Related membership not found".format(
                                partner.id
                            )
                        )
                    )
                membership_voluntary_shares = (
                    related_partner_membership.share_ids.filtered(
                        lambda share_line: share_line.share_product_id.id
                        == voluntary_share_product.id
                    )
                )
                for membership_voluntary_share in membership_voluntary_shares:
                    total_in_membership += membership_voluntary_share.total_amount_line
                if total_in_membership != total_in_account_move:
                    raise ValidationError(
                        "ERROR on Membership {}. Invoice total not matching share lines".format(
                            related_partner_membership.id
                        )
                    )

    def _find_related_invoice_line_from_share_line(self, share_line):
        return self.env["account.move.line"].search(
            [
                ("move_id.partner_id", "=", share_line.partner_id.id),
                ("move_id.company_id", "=", share_line.company_id.id),
                ("move_id.payment_state", "=", "paid"),
                ("price_subtotal", "=", share_line.total_amount_line),
                ("product_id", "=", share_line.share_product_id.id),
            ]
        )
