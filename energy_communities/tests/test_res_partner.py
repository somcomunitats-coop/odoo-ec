from unittest import skip

from odoo.tests import common

from ..wizards.create_users_wizard import CreateUsersWizard


@skip("Not necessary")
class TestCreateUsersWizard(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_execute__ok(self):
        # given a partner that is already a member
        partner = self.env["res.partner"].search([("vat", "=", "26309903L")], limit=1)[
            0
        ]

        # when we invite that partner to become user
        create_user_wiz = CreateUsersWizard({"action": "create_kc_user"})
        res = create_user_wiz.execute()

        # then an user to keycloak is created
        self.assertEqual(res, [])
