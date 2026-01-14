import unittest

from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestContract(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.contract = self.env["contract.contract"].search(
            [("id", "=", 567)], limit=1
        )[0]
        self.user = self.env["res.users"].search([("id", "=", 292)], limit=1)[
            0
        ]  # Alvaro Garcia

    # TODO: Move to testing scenarios (Now apply to dev1 with custom modifications)
    @unittest.skip("skip")
    def test_contract_numberof_effective_cooperators_ok(self):
        self.assertEqual(
            self.contract.with_company(self.env.ref("base.main_company"))
            .with_user(self.user)
            .get_numberof_effective_cooperators_range(),
            1,
        )

        invoice = (
            self.contract.with_company(self.env.ref("base.main_company"))
            .with_user(self.user)
            .recurring_create_invoice()
        )
        self.assertEqual(
            invoice[0]
            .with_company(self.env.ref("base.main_company"))
            .with_user(self.user)
            .line_ids[0]
            .quantity,
            1,
        )
        self.assertEqual(
            invoice[0]
            .with_company(self.env.ref("base.main_company"))
            .with_user(self.user)
            .line_ids[0]
            .quantity,
            self.contract.with_company(self.env.ref("base.main_company"))
            .with_user(self.user)
            .get_numberof_effective_cooperators_range(),
        )
