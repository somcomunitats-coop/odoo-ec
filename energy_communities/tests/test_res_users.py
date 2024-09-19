from unittest.mock import patch

from faker import Faker

from odoo.exceptions import UserError, ValidationError
from odoo.tests import common

from .helpers import CompanySetupMixin, UserSetupMixin

faker = Faker(locale="es_ES")


class TestResUsers(CompanySetupMixin, UserSetupMixin, common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.users_model = self.env["res.users"]
        self.company_model = self.env["res.company"]
        self.role_line_model = self.env["res.users.role.line"]
        self.instance = self.company_model.search(
            [("hierarchy_level", "=", "instance")]
        )[0]

        self.coordination = self.create_company(
            "Coordinator",
            "coordinator",
            self.instance.id,
        )
        self.community = self.create_company(
            "Energy Community",
            "community",
            self.coordination.id,
        )

        self.platform_admin = self.create_user("Platform", "Admin")
        self.community_admin = self.create_user("Community", "Admin")
        self.coord_admin = self.create_user("Coord", "Admin")
        self.random_user = self.create_user("Brandom", "Random")

        self.make_community_admin(self.community_admin)
        self.make_coord_admin(self.coord_admin)

    @patch(
        "odoo.addons.energy_communities.models.res_users.ResUsers.create_users_on_keycloak"
    )
    @patch(
        "odoo.addons.energy_communities.models.res_users.ResUsers._send_kc_reset_password_mail"
    )
    def test__create_energy_community_base_user__base_case(
        self, reset_password_mocked, create_kc_user_mocked
    ):
        user = self.users_model.create_energy_community_base_user(
            vat=faker.vat_id(),
            first_name="Tom",
            last_name="Bombadil",
            lang_code="en_US",
            email=faker.email(),
        )

        # then _send_kc_reset_password_mail function was called once time
        reset_password_mocked.assert_called_once()
        # then create_users_on_keycloak function was called once time
        create_kc_user_mocked.assert_called_once()

    @patch("odoo.addons.energy_communities.models.res_users.ResUsers.make_ce_user")
    def test__add_energy_community_role__make_ce_user(self, make_ce_user_mocked):
        self.random_user.add_energy_community_role(self.community.id, "role_ce_admin")

        # then make_ce_user_mocked function was called once time
        make_ce_user_mocked.assert_called_with(self.community.id, "role_ce_admin")

    @patch("odoo.addons.energy_communities.models.res_users.ResUsers.make_coord_user")
    def test__add_energy_community_role__make_coord_user(self, make_coord_user_mocked):
        self.random_user.add_energy_community_role(
            self.coordination.id, "role_coord_admin"
        )

        # then make_coord_user function was called once time
        make_coord_user_mocked.assert_called_with(
            self.coordination.id, "role_coord_admin"
        )

    def test__add_energy_community_role__role_not_found(self):
        with self.assertRaises(UserError):
            self.users_model.add_energy_community_role(
                role_name="onering_owner",
                company_id=self.coordination.id,
            )

    def test__make_ce_user__already_user(self):
        self.community_admin.make_ce_user(self.community.id, "role_ce_member")
        rl = self.role_line_model.search(
            [
                ("user_id", "=", self.community_admin.id),
                ("company_id", "=", self.community.id),
            ]
        )
        self.assertEqual(len(rl), 1)
        self.assertEqual(rl[0].role_id.code, "role_ce_member")
        self.assertIn(self.community, self.community_admin.company_ids)

    def test__make_ce_user__new_user(self):
        self.random_user.make_ce_user(self.community.id, "role_ce_member")
        rl = self.role_line_model.search(
            [
                ("user_id", "=", self.random_user.id),
                ("role_id.code", "=", "role_ce_member"),
                ("company_id", "=", self.community.id),
            ]
        )
        self.assertEqual(len(rl), 1)
        self.assertIn(self.community, self.random_user.company_ids)

    def test__make_internal_user__new_user(self):
        # When we call make_internal_user with a new user
        self.random_user.make_internal_user()

        # Then creates new role_line with "role_internal_user"
        role_lines = self.role_line_model.search(
            [
                ("user_id", "=", self.random_user.id),
                ("role_id.code", "=", "role_internal_user"),
            ]
        )
        self.assertEqual(len(role_lines), 1)
        role_line = role_lines[0]
        # and role_line has not company
        self.assertEqual(list(role_line.company_id), [])

    def test__make_internal_user__already_user(self):
        # When we call make_internal_user with existing user
        self.community_admin.make_internal_user()

        # Then anything is created
        rl = self.role_line_model.search(
            [
                ("user_id", "=", self.community_admin.id),
                ("role_id.code", "=", "role_internal_user"),
            ]
        )
        self.assertEqual(len(rl), 1)

    def test__make_coord_user__new_user(self):
        self.random_user.make_coord_user(self.coordination.id, "role_coord_admin")

        rl_coord = self.role_line_model.search(
            [
                ("user_id", "=", self.random_user.id),
                ("role_id.code", "=", "role_coord_admin"),
                ("company_id", "=", self.coordination.id),
            ]
        )
        self.assertEqual(len(rl_coord), 1)
        self.assertIn(self.coordination, self.random_user.company_ids)
        rl_ce = self.role_line_model.search(
            [
                ("user_id", "=", self.random_user.id),
                ("role_id.code", "=", "role_ce_manager"),
                ("company_id", "=", self.community.id),
            ]
        )
        self.assertEqual(len(rl_ce), 1)
        self.assertIn(self.community, self.random_user.company_ids)

    def test__make_coord_user__already_user(self):
        other_coord = self.create_company(
            "Coordinator 2",
            "coordinator",
            self.instance.id,
        )

        self.coord_admin.make_coord_user(other_coord.id, "role_coord_admin")

        rl_coord = self.role_line_model.search(
            [
                ("user_id", "=", self.coord_admin.id),
                ("role_id.code", "=", "role_coord_admin"),
            ]
        )
        self.assertEqual(len(rl_coord), 2)
        self.assertIn(self.coordination, self.coord_admin.company_ids)
        self.assertIn(other_coord, self.coord_admin.company_ids)
