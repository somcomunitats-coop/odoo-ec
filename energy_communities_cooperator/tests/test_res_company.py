import unittest

from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestResCompany(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.company = self.env["res.company"].search([("id", "=", 3)], limit=1)[
            0
        ]  # Gares Bide
        self.user = self.env["res.users"].search([("id", "=", 292)], limit=1)[
            0
        ]  # Alvaro Garcia

    # TODO: Move to testing scenarios (Now apply to dev1 with custom modifications)
    @unittest.skip("skip")
    def test_res_company_users_metrics_ok(self):
        self.assertEqual(
            self.company.with_company(self.env.ref("base.main_company"))
            .with_user(self.user)
            .numberof_effective_inviteds,
            8,
        )
        self.assertEqual(
            self.company.with_company(self.env.ref("base.main_company"))
            .with_user(self.user)
            .numberof_effective_members,
            97,
        )
        self.assertEqual(
            self.company.with_company(self.env.ref("base.main_company"))
            .with_user(self.user)
            .numberof_effective_cooperators,
            105,
        )
