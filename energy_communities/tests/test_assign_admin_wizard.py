from unittest.mock import patch

from faker import Faker

from odoo.exceptions import ValidationError
from odoo.tests import common

from .helpers import UserSetupMixin

faker = Faker(locale="es_ES")


class TestAssingAdminWizard(UserSetupMixin, common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.users_model = self.env["res.users"]
        self.company_model = self.env["res.company"]

        self.random_user = self.create_user("Brandom", "Random", "43217763G")

    @patch(
        "odoo.addons.energy_communities.models.res_users.ResUsers.add_energy_community_role"
    )
    def test__process_data__search_user_case_insensitive(
        self, add_energy_community_role_mocked
    ):
        wizard = self.env["assign.admin.wizard"].create(
            {
                "is_new_admin": False,
                "vat": "43217763g",
            }
        )
        wizard.process_data()

        add_energy_community_role_mocked.assert_called_once()

    def test__process_data__user_not_found(self):
        # When we search a new user
        wizard = self.env["assign.admin.wizard"].create(
            {
                "is_new_admin": False,
                "vat": "43217761g",
            }
        )

        # Raises User not found error
        with self.assertRaises(ValidationError):
            wizard.process_data()
