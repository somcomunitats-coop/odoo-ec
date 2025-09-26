from unittest import skip

from odoo.tests.common import TransactionCase


class TestAccountMove(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    @skip(
        "This test must be adjusted to demo data as all others on this module use it."
    )
    def test_invoice_service_type(self):
        # Given a set of invoices
        test_cases = {
            "selfconsumption": 18212,
            "other": 16189,
        }
        # When we calculate its service type
        for expect_value, invoice_id in test_cases.items():
            invoice = self.env["account.move"].with_company(29).browse(invoice_id)
            service_type = invoice.service_type
            # Then, it's type is selfconsumption
            self.assertEqual(
                service_type,
                expect_value,
                f"Service type {service_type} is not the expected for invoice {invoice_id}",
            )
