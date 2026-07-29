from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests import Form, common, tagged

from odoo.addons.energy_communities_cooperator.config import (
    COOP_SHARE_PRODUCT_CATEG_REF,
    COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF,
)


@tagged("-at_install", "post_install")
class TestVoluntaryShareInterestReturn(common.TransactionCase):
    """
    Tests for VoluntaryShareInterestReturnWizard.

    Verifies that both _get_voluntary_shares_invoice_line and
    _consistency_validation identify products by category + company,
    without depending on res.company.voluntary_share_id.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref(
            "energy_communities.energy_community_company_1_wizard"
        ).new_company_id
        cls.voluntary_categ = cls.env.ref(COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF)
        cls.regular_categ = cls.env.ref(COOP_SHARE_PRODUCT_CATEG_REF)

        # Ensure the wizard no longer depends on this company field.
        cls.company.voluntary_share_id = False

        cls.voluntary_product_a = cls._create_share_product(
            "VSIR Test Voluntary Share A", cls.voluntary_categ, list_price=100.0
        )
        cls.voluntary_product_b = cls._create_share_product(
            "VSIR Test Voluntary Share B", cls.voluntary_categ, list_price=200.0
        )
        cls.regular_product = cls._create_share_product(
            "VSIR Test Regular Share", cls.regular_categ, list_price=50.0
        )

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "VSIR Test Partner",
                "email": "vsir.test@example.com",
            }
        )
        cls.membership = cls.partner.with_company(
            cls.company
        ).create_cooperative_membership(cls.company)

        # Paid invoices — needed by _consistency_validation
        cls.invoice_a = cls._create_paid_invoice(cls.voluntary_product_a, 100.0)
        cls.invoice_b = cls._create_paid_invoice(cls.voluntary_product_b, 200.0)
        cls.invoice_regular = cls._create_paid_invoice(cls.regular_product, 50.0)

        cls.invoice_line_a = cls.invoice_a.invoice_line_ids[0]
        cls.invoice_line_b = cls.invoice_b.invoice_line_ids[0]
        cls.invoice_line_regular = cls.invoice_regular.invoice_line_ids[0]

        cls.share_line_a = cls._create_share_line(
            cls.voluntary_product_a,
            cls.invoice_line_a,
            share_number=1,
            unit_price=100.0,
            effective_date=cls.invoice_a.payment_date or date.today(),
        )
        cls.share_line_b = cls._create_share_line(
            cls.voluntary_product_b,
            cls.invoice_line_b,
            share_number=1,
            unit_price=200.0,
            effective_date=cls.invoice_b.payment_date or date.today(),
        )
        cls.share_line_regular = cls._create_share_line(
            cls.regular_product,
            cls.invoice_line_regular,
            share_number=1,
            unit_price=50.0,
            effective_date=cls.invoice_regular.payment_date or date.today(),
        )

        cls.wizard = (
            cls.env["voluntary.share.interest.return.wizard"]
            .with_company(cls.company)
            .create({"company_id": cls.company.id})
        )

    @classmethod
    def _create_share_product(cls, name, categ, list_price):
        template = cls.env["product.template"].create(
            {
                "name": name,
                "detailed_type": "service",
                "is_share": True,
                "list_price": list_price,
                "categ_id": categ.id,
                "company_id": cls.company.id,
                "by_individual": True,
                "by_company": True,
            }
        )
        return template.product_variant_id

    @classmethod
    def _create_paid_invoice(cls, product, price_unit):
        journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "purchase")], limit=1
        )
        move = (
            cls.env["account.move"]
            .with_company(cls.company)
            .create(
                {
                    "move_type": "in_invoice",
                    "partner_id": cls.partner.id,
                    "company_id": cls.company.id,
                    "journal_id": journal.id,
                    "invoice_date": date.today(),
                    "membership_id": cls.membership.id,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": product.id,
                                "quantity": 1,
                                "price_unit": price_unit,
                                "name": product.name,
                            },
                        )
                    ],
                }
            )
        )
        move.action_post()
        cls._pay_invoice(move)
        return move

    @classmethod
    def _pay_invoice(cls, invoice):
        payment_form = Form(
            cls.env["account.payment.register"].with_context(
                active_ids=[invoice.id], active_model="account.move"
            )
        )
        payment_form.payment_date = date.today()
        payment_form.save().action_create_payments()

    @classmethod
    def _create_share_line(
        cls, product, invoice_line, share_number, unit_price, effective_date
    ):
        return cls.env["share.line"].create(
            {
                "share_product_id": product.id,
                "share_number": share_number,
                "share_unit_price": unit_price,
                "partner_id": cls.partner.id,
                "company_id": cls.company.id,
                "effective_date": effective_date,
                "related_invoice_line": invoice_line.id,
            }
        )

    # --- _get_voluntary_shares_invoice_line ---

    def test_get_invoice_line_uses_category_not_company_field(self):
        """_get_voluntary_shares_invoice_line works without voluntary_share_id."""
        self.assertFalse(self.company.voluntary_share_id)

        voluntary_shares = self.wizard._get_voluntary_shares_invoice_line()

        self.assertIn(self.membership.id, voluntary_shares)
        found_lines = voluntary_shares[self.membership.id]
        self.assertIn(self.invoice_line_a, found_lines)
        self.assertIn(self.invoice_line_b, found_lines)
        self.assertNotIn(self.invoice_line_regular, found_lines)

    def test_get_invoice_line_finds_all_voluntary_products(self):
        """_get_voluntary_shares_invoice_line returns lines for all voluntary products."""
        voluntary_shares = self.wizard._get_voluntary_shares_invoice_line()
        found_lines = voluntary_shares[self.membership.id]

        self.assertEqual(len(found_lines), 2)
        self.assertEqual(
            {line.product_id.id for line in found_lines},
            {self.voluntary_product_a.id, self.voluntary_product_b.id},
        )

    # --- _consistency_validation ---

    def test_consistency_validation_passes_with_valid_data(self):
        """_consistency_validation raises no error when data is consistent."""
        try:
            self.wizard._consistency_validation()
        except ValidationError as e:
            self.fail(f"_consistency_validation raised unexpectedly: {e}")

    def test_consistency_validation_ignores_regular_shares(self):
        """_consistency_validation does not validate non-voluntary share lines."""
        # Remove the related_invoice_line from the regular share — if the method
        # considered it, it would raise "no related invoice line".
        self.share_line_regular.related_invoice_line = False
        try:
            self.wizard._consistency_validation()
        except ValidationError as e:
            self.fail(
                f"_consistency_validation should ignore regular shares but raised: {e}"
            )
        finally:
            self.share_line_regular.related_invoice_line = self.invoice_line_regular

    def test_consistency_validation_raises_when_no_invoice_line(self):
        """_consistency_validation raises if a voluntary share has no related invoice.

        We create a share line for an orphan product (no paid invoice anywhere)
        so neither the related_invoice_line field nor the fallback search can
        resolve it, forcing the ValidationError.
        """
        orphan_product = self._create_share_product(
            "VSIR Orphan Voluntary Share", self.voluntary_categ, list_price=999.0
        )
        orphan_share = self.env["share.line"].create(
            {
                "share_product_id": orphan_product.id,
                "share_number": 1,
                "share_unit_price": 999.0,
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "effective_date": date.today(),
                # no related_invoice_line — and no paid invoice exists for this product
            }
        )
        with self.assertRaises(ValidationError):
            self.wizard._consistency_validation()
        orphan_share.unlink()
