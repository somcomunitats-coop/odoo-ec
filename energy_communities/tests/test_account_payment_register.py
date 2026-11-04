import unittest
from datetime import date

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountPaymentRegisterInvoiceDate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        bank_journal = cls.env["account.journal"].search(
            [("type", "in", ("bank", "cash"))], limit=1
        )
        if not bank_journal:
            raise unittest.SkipTest("No bank or cash journal is installed")
        cls.company = bank_journal.company_id
        cls.bank_journal = bank_journal
        cls.company.sudo().write(
            {
                "fiscalyear_lock_date": False,
                "period_lock_date": False,
                "tax_lock_date": False,
            }
        )
        receivable = cls.env["account.account"].search(
            [
                ("company_id", "=", cls.company.id),
                ("account_type", "=", "asset_receivable"),
                ("deprecated", "=", False),
            ],
            limit=1,
        )
        income = cls.env["account.account"].search(
            [
                ("company_id", "=", cls.company.id),
                ("account_type", "=", "income"),
                ("deprecated", "=", False),
            ],
            limit=1,
        )
        if not receivable or not income:
            raise unittest.SkipTest("Company chart of accounts is incomplete")
        cls.receivable = receivable
        cls.income = income
        country = cls.env.ref("base.es", raise_if_not_found=False)
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mass payment partner",
                "company_id": cls.company.id,
                "country_id": country.id if country else False,
            }
        )
        cls.partner.with_company(cls.company).write(
            {
                "property_account_receivable_id": receivable.id,
                "customer_payment_mode_id": False,
                "supplier_payment_mode_id": False,
            }
        )

    def _create_invoice(self, partner, invoice_date, amount=100.0):
        invoice = (
            self.env["account.move"]
            .with_company(self.company)
            .create(
                {
                    "move_type": "out_invoice",
                    "partner_id": partner.id,
                    "invoice_date": invoice_date,
                    "company_id": self.company.id,
                    "payment_mode_id": False,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "name": "Historical share",
                                "quantity": 1,
                                "price_unit": amount,
                                "account_id": self.income.id,
                                "tax_ids": [Command.clear()],
                            }
                        )
                    ],
                }
            )
        )
        invoice.action_post()
        return invoice

    def _register(self, invoices, **vals):
        wizard = (
            self.env["account.payment.register"]
            .with_company(self.company)
            .with_context(
                active_model="account.move",
                active_ids=invoices.ids,
            )
            .create(vals)
        )
        return wizard._create_payments()

    def test_payment_date_follows_each_invoice_date(self):
        first = self._create_invoice(self.partner, date(2026, 1, 15))
        other_partner = self.partner.copy({"name": "Other mass payment partner"})
        second = self._create_invoice(other_partner, date(2026, 3, 2), amount=50.0)

        payments = self._register(
            first + second,
            payment_date_equals_invoice_date=True,
            payment_date=date(2026, 11, 4),
        )

        self.assertEqual(len(payments), 2)
        self.assertEqual(first._get_reconciled_payments().date, date(2026, 1, 15))
        self.assertEqual(second._get_reconciled_payments().date, date(2026, 3, 2))
        self.assertEqual(first.payment_state, "paid")
        self.assertEqual(second.payment_state, "paid")
        self.assertEqual(first.payment_date, date(2026, 1, 15))
        self.assertEqual(second.payment_date, date(2026, 3, 2))

    def test_wizard_payment_date_is_kept_when_flag_is_disabled(self):
        first = self._create_invoice(self.partner, date(2026, 1, 15))
        other_partner = self.partner.copy({"name": "Wizard date partner"})
        second = self._create_invoice(other_partner, date(2026, 3, 2))
        wizard_date = date(2026, 11, 1)

        payments = self._register(
            first + second,
            payment_date_equals_invoice_date=False,
            payment_date=wizard_date,
        )

        self.assertEqual(set(payments.mapped("date")), {wizard_date})

    def test_grouped_invoices_are_paid_separately_on_their_invoice_date(self):
        first = self._create_invoice(self.partner, date(2026, 2, 1), amount=10.0)
        second = self._create_invoice(self.partner, date(2026, 4, 1), amount=20.0)
        wizard = (
            self.env["account.payment.register"]
            .with_company(self.company)
            .with_context(
                active_model="account.move",
                active_ids=(first + second).ids,
            )
            .create(
                {
                    "payment_date_equals_invoice_date": True,
                    "group_payment": True,
                }
            )
        )
        wizard.group_payment = True

        payments = wizard._create_payments()

        self.assertEqual(len(payments), 2)
        self.assertEqual(first._get_reconciled_payments().date, date(2026, 2, 1))
        self.assertEqual(second._get_reconciled_payments().date, date(2026, 4, 1))

    def test_missing_invoice_date_raises(self):
        misc_journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "general")],
            limit=1,
        )
        move = (
            self.env["account.move"]
            .with_company(self.company)
            .create(
                {
                    "move_type": "entry",
                    "date": date(2026, 1, 15),
                    "journal_id": misc_journal.id,
                    "company_id": self.company.id,
                    "line_ids": [
                        Command.create(
                            {
                                "name": "Receivable without invoice date",
                                "account_id": self.receivable.id,
                                "partner_id": self.partner.id,
                                "debit": 25.0,
                                "credit": 0.0,
                            }
                        ),
                        Command.create(
                            {
                                "name": "Counterpart",
                                "account_id": self.income.id,
                                "debit": 0.0,
                                "credit": 25.0,
                            }
                        ),
                    ],
                }
            )
        )
        move.action_post()
        wizard = (
            self.env["account.payment.register"]
            .with_company(self.company)
            .with_context(active_model="account.move", active_ids=move.ids)
            .create({"payment_date_equals_invoice_date": True})
        )

        with self.assertRaises(UserError):
            wizard._create_payments()
