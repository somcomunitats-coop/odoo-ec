from odoo.addons.component.core import WorkContext
from odoo.addons.component.tests.common import TransactionComponentCase

from ...components import UserCreator


class TestUserCreator(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        company = self.env["res.company"].search(
            [("name", "=", "Community 1")], limit=1
        )[0]
        self.backend = self.env["utils.backend"].with_company(company).browse(1)

        self.user_creator_component = WorkContext(
            "res.users", collection=self.backend
        ).component(usage="user.create")
        assert isinstance(
            self.user_creator_component, UserCreator
        ), "self.user_creator_component hast to be an instance of UserCreator component"

        self.role_id = self.env.ref("energy_communities.role_ce_member")
        self.vat = "43549978F"
        # self.vat = "26309903L"

    def test_create_users_from_cooperator_partners__ok(self):
        # given a partner that is an efective cooperator
        partner = self.env["res.partner"].search([("vat", "=", self.vat)], limit=1)[0]

        # when we create the user in kc related with that partner
        self.user_creator_component.create_users_from_cooperator_partners(
            [partner], self.role_id, "invite_user_through_kc", True
        )
        # Then a new user is created
        user = self.env["res.users"].search([("login", "=", partner.vat)])

        self.assertEqual(user.login, partner.vat)
