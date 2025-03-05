from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

_DEFAULT_ANUAL_BULK_INTEREST_RATE = 1
_DEFAULT_IRPF_CAPITAL_TAX_XMLID = "account_tax_template_p_irpf19"
_DEFAULT_CREDIT_ACCOUNT_MOVE_XMLID = "account_common_4100"
_DEFAULT_RETURN_ACCOUNT_MOVE_LINE_XMLID = "account_common_6624"
# NOTE: we'll have to build this xml_ids dynamically prepending on each "l10n_es.{company_id}_"


class VoluntaryShareInterestReturnWizard(models.TransientModel):
    _name = "voluntary.share.interest.return.wizard"
    _description = "Calculate and prepare interests to be returned in voluntary shares"

    company_id = fields.Many2one("res.company")
    interest = fields.Float(string="Interest")
    credit_account_move_id = fields.Many2one(
        "account.account",
        string="Account move credit account",
    )
    return_line_account_id = fields.Many2one(
        "account.account",
        string="Return line account",
    )
    journal_id = fields.Many2one("account.journal", string="Journal")
    tax_id = fields.Many2one("account.tax", string="Tax")
    payment_mode_id = fields.Many2one("account.payment.mode", string="Payment mode")
    start_date_period = fields.Date(string="Period start date")
    end_date_period = fields.Date(string="Period end date")
    invoice_date = fields.Date(string="Invoice date")
    invoice_date_due = fields.Date(string="Invoice due date")

    # Only way we've found to setup defaults based on company is by getting it from currently selected one.
    def default_get(self, fields):
        res = super().default_get(fields)
        res.update(
            {
                "interest": _DEFAULT_ANUAL_BULK_INTEREST_RATE,
                "credit_account_move_id": self._default_obj_id_by_ref(
                    _DEFAULT_CREDIT_ACCOUNT_MOVE_XMLID
                ),
                "return_line_account_id": self._default_obj_id_by_ref(
                    _DEFAULT_RETURN_ACCOUNT_MOVE_LINE_XMLID
                ),
                "tax_id": self._default_obj_id_by_ref(_DEFAULT_IRPF_CAPITAL_TAX_XMLID),
                "journal_id": self.env.company.voluntary_share_journal_account.id
                or False,
                "start_date_period": self._default_period_date("start"),
                "end_date_period": self._default_period_date("end"),
                "invoice_date": datetime.now(),
                "invoice_date_due": datetime.now(),
                "company_id": self.env.company.id,
            }
        )
        return res

    def _default_period_date(self, mode):
        # return (datetime.now() - timedelta(days=365)).replace(day=1,month=1)
        if mode == "start":
            return datetime.now() - timedelta(days=365)
        if mode == "end":
            return datetime.now()

    def _build_l10n_multicompany_xml_id(self, base_ref):
        return "l10n_es.{company_id}_{ref}".format(
            company_id=self.env.company.id, ref=base_ref
        )

    def _default_obj_id_by_ref(self, base_ref):
        return self.env.ref(
            self._build_l10n_multicompany_xml_id(base_ref),
            raise_if_not_found=True,
        ).id

    def execute_return(self):
        self._consistency_validation()
        voluntary_share_interest_return = self.env[
            "voluntary.share.interest.return"
        ].create(
            {
                "name": "{company_name} voluntary share interest return from {start_date_period} to {end_date_period}".format(
                    company_name=self.company_id.name,
                    start_date_period=self.start_date_period,
                    end_date_period=self.end_date_period,
                ),
                "start_date_period": self.start_date_period,
                "end_date_period": self.end_date_period,
                "payment_mode_id": self.payment_mode_id.id,
            }
        )
        self._generate_related_invoices(voluntary_share_interest_return.id)
        # TODO: Should we post a message?
        return {
            "type": "ir.actions.act_window",
            "name": _("Return voluntary shares interest"),
            "res_model": "voluntary.share.interest.return",
            "view_type": "form",
            "view_mode": "form",
            "target": "current",
            "res_id": voluntary_share_interest_return.id,
        }

    def _get_voluntary_shares_invoice_line(self):
        voluntary_shares = {}
        voluntary_share_product_template = self.company_id.voluntary_share_id
        # TODO: We're assuming there is only one product.product for it's product.template
        voluntary_share_product = self.env["product.product"].search(
            [("product_tmpl_id", "=", voluntary_share_product_template.id)], limit=1
        )
        memberships = self.env["cooperative.membership"].search(
            [("company_id", "=", self.company_id.id)]
        )
        for membership in memberships:
            membership_voluntary_shares = membership.share_ids.filtered(
                lambda share_line: share_line.share_product_id.id
                == voluntary_share_product.id
            )
            if membership_voluntary_shares:
                for membership_voluntary_share in membership_voluntary_shares:
                    related_invoice_line = (
                        self._find_related_invoice_line_from_share_line(
                            membership_voluntary_share
                        )
                    )
                    if membership.id in voluntary_shares.keys():
                        voluntary_shares[membership.id].append(related_invoice_line)
                    else:
                        voluntary_shares[membership.id] = [related_invoice_line]
        return voluntary_shares

    def _generate_related_invoices(self, voluntary_share_interest_return_id):
        voluntary_shares = self._get_voluntary_shares_invoice_line()
        if voluntary_shares:
            for membership_id in voluntary_shares.keys():
                invoice = self._create_interest_return_invoice(
                    membership_id,
                    voluntary_shares[membership_id],
                    voluntary_share_interest_return_id,
                )

    def _create_interest_return_invoice(
        self,
        membership_id,
        voluntary_shares_inv_line,
        voluntary_share_interest_return_id,
    ):
        inv_creation_dict = self._prepare_inv_create_dict(
            membership_id, voluntary_shares_inv_line, voluntary_share_interest_return_id
        )
        # empty inv_creation_dict means the invoice to be created is without lines (all lines out of period)
        if inv_creation_dict:
            invoice = self.env["account.move"].create(inv_creation_dict)

    def _prepare_inv_create_dict(
        self,
        membership_id,
        voluntary_shares_inv_line,
        voluntary_share_interest_return_id,
    ):
        membership = self.env["cooperative.membership"].browse(membership_id)
        create_dict = {
            "partner_id": membership.partner_id.id,
            "date": self.invoice_date,
            "invoice_date": self.invoice_date,
            "invoice_date_due": self.invoice_date_due,
            "journal_id": self.journal_id.id,
            "payment_mode_id": self.payment_mode_id.id,
            "company_id": self.company_id.id,
            "move_type": "in_invoice",
            "partner_bank_id": self._get_invoice_partner_bank(
                voluntary_shares_inv_line[-1]
            ),  # TODO: Find a proper way of getting partner bank account
            "voluntary_share_interest_return_id": voluntary_share_interest_return_id,
            "invoice_line_ids": [],
        }
        total_contribution = 0
        for voluntary_share_inv_line in voluntary_shares_inv_line:
            inv_line_create_dict = self._prepare_inv_line_create_dict(
                voluntary_share_inv_line
            )
            if inv_line_create_dict:
                create_dict["invoice_line_ids"].append((0, 0, inv_line_create_dict))
                total_contribution += voluntary_share_inv_line.price_subtotal
        create_dict["voluntary_share_total_contribution"] = total_contribution
        # We won't generate an invoice without a total contribution. (all lines out of period)
        if total_contribution > 0:
            return create_dict
        return False

    def _get_invoice_partner_bank(self, origin_inv_line):
        # TODO: This method must take into consideration that the bank account has a valid mandate
        origin_inv = origin_inv_line.move_id
        if origin_inv_line.move_id.partner_bank_id:
            return origin_inv.partner_bank_id.id
        else:
            rel_bank_acc = self.env["res.partner.bank"].search(
                [("partner_id", "=", origin_inv.partner_id.id)]
            )
            if rel_bank_acc:
                return rel_bank_acc[0].id
        return False

    def _prepare_inv_line_create_dict(self, origin_inv_line):
        days_quantity = self._get_voluntary_share_days_num(origin_inv_line)
        period_start_date = self._get_period_start_date(origin_inv_line)
        # Negative quantity values implies payment date > end_period => line outside calculation period.
        # We don't want to create those lines
        if days_quantity > 0:
            return {
                "name": """Voluntary share interest return
                    contribution ref: [{inv_name}] #{inv_id}
                    contribution line ref: #{inv_line_id}
                    Period: from {period_start} to {period_end}
                    Interest: {interest}%
                    Price: {total_days} days * {price_unit_day} €/day
                """.format(
                    inv_id=origin_inv_line.move_id.id,
                    inv_line_id=origin_inv_line.id,
                    inv_name=origin_inv_line.move_id.name,
                    period_start=period_start_date.strftime("%d/%m/%Y"),
                    period_end=self.end_date_period.strftime("%d/%m/%Y"),
                    interest=self.interest,
                    total_days=days_quantity,
                    price_unit_day="%.5f"
                    % self._get_voluntary_share_price_unit_per_day(origin_inv_line),
                ),
                "account_id": self.return_line_account_id.id,
                "quantity": 1,
                "price_unit": self._get_voluntary_share_price_unit(origin_inv_line),
                "voluntary_share_return_start_date_period": period_start_date,
                "voluntary_share_return_end_date_period": self.end_date_period,
                "voluntary_share_contribution": origin_inv_line.price_subtotal,
                "voluntary_share_interest": self.interest,
                "journal_id": self.journal_id.id,
                "company_id": self.company_id.id,
                "tax_ids": [(4, self.tax_id.id)],
            }
        return False

    def _get_period_start_date(self, inv_line):
        payment_date = inv_line.move_id.payment_date
        if payment_date >= self.start_date_period:
            return payment_date
        else:
            return self.start_date_period

    # TODO: verify this formula
    # TODO: Calculate end period based on a possible return.
    def _get_voluntary_share_days_num(self, inv_line):
        return (self.end_date_period - self._get_period_start_date(inv_line)).days

    def _get_voluntary_share_price_unit(self, inv_line):
        days_quantity = self._get_voluntary_share_days_num(inv_line)
        price_unit_day = self._get_voluntary_share_price_unit_per_day(inv_line)
        return price_unit_day * days_quantity

    def _get_voluntary_share_price_unit_per_day(self, inv_line):
        return inv_line.price_subtotal * self.interest / 36500

    def _find_related_invoice_line_from_share_line(self, share_line):
        if share_line.related_invoice_line:
            return share_line.related_invoice_line
        return self.env["account.move.line"].search(
            [
                ("move_id.partner_id", "=", share_line.partner_id.id),
                ("move_id.company_id", "=", share_line.company_id.id),
                ("move_id.payment_state", "=", "paid"),
                ("price_subtotal", "=", share_line.total_amount_line),
                ("product_id", "=", share_line.share_product_id.id),
            ]
        )

    def _consistency_validation(self):
        if self.env.company.id != self.company_id.id:
            raise ValidationError(
                "The company on your context must be the same as the one you're executing the action for"
            )

        voluntary_share_product = self.company_id.voluntary_share_id
        # check if all shares comes from an invoice
        memberships = self.env["cooperative.membership"].search(
            [("company_id", "=", self.company_id.id)]
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
                if (
                    related_invoice_line.move_id.payment_date
                    != membership_voluntary_share.effective_date
                ):
                    raise ValidationError(
                        _(
                            "ERROR on Membership {membership_id}. Inconstency between share {share_id} effective date and related invoice payment_date".format(
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
            .search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("payment_state", "=", "paid"),
                ]
            )
            .mapped("partner_id")
        )
        for partner in company_invoices_partners:
            if partner.cooperator:
                total_in_account_move = 0
                total_in_membership = 0
                partner_company_invoices = self.env["account.move"].search(
                    [
                        ("company_id", "=", self.company_id.id),
                        ("payment_state", "=", "paid"),
                        ("partner_id", "=", partner.id),
                        ("membership_id", "!=", None),
                    ]
                )
                for line in partner_company_invoices.invoice_line_ids.filtered(
                    lambda invoice_line: invoice_line.product_id.id
                    == voluntary_share_product.id
                ):
                    if line.move_id.membership_id.company_id.id != self.company_id.id:
                        raise ValidationError(
                            _(
                                "ERROR on Invoice {}. Related membership not in same company".format(
                                    line.move_id.id
                                )
                            )
                        )
                    total_in_account_move += line.price_subtotal
                related_partner_membership = self.env["cooperative.membership"].search(
                    [
                        ("company_id", "=", self.company_id.id),
                        ("partner_id", "=", partner.id),
                    ]
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
