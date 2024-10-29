from unittest.mock import patch

from faker import Faker

from odoo.exceptions import ValidationError
from odoo.tests import common

from .helpers import CompanySetupMixin, UserSetupMixin

faker = Faker(locale="es_ES")


class TestMultiEasyCreation(UserSetupMixin, CompanySetupMixin, common.TransactionCase):
    def create_crm_lead(self):
        return self.env["crm.lead"].create(
            {
                "name": "CE Name",
                "email_from": faker.email(),
                "submission_type": "place_submission",
                "company_id": self.coordination.id,
                "source_id": self.env.ref(
                    "energy_communities.ce_source_creation_ce_proposal"
                ).id,
                "metadata_line_ids": [
                    (0, 0, {"key": "current_lang", "value": "ca"}),
                    (0, 0, {"key": "ce_creation_date", "value": "1994-09-01"}),
                    (0, 0, {"key": "ce_address", "value": "Av St Narcís"}),
                    (0, 0, {"key": "ce_city", "value": "Girona"}),
                    (0, 0, {"key": "ce_zip", "value": "17005"}),
                    (0, 0, {"key": "contact_phone", "value": "666666666"}),
                    (0, 0, {"key": "email_from", "value": "random@somcomunitats.coop"}),
                    (0, 0, {"key": "ce_vat", "value": "38948723V"}),
                ],
            }
        )

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

        self.coord_admin = self.create_user("Coord", "Admin")

        self.make_coord_user(self.coordination, self.coord_admin)

        self.crm_lead = self.create_crm_lead()
        self.wizard = self.env["account.multicompany.easy.creation.wiz"].create(
            self.crm_lead.get_default_community_wizard()
        )

    def test__action_accept__company_created(self):
        self.wizard.action_accept()

        companies = self.env["res.company"].search(
            [("parent_id", "=", self.coordination.id)]
        )
        self.assertEqual(len(companies), 1)
        company = companies[0]
        self.assertEqual(company.hierarchy_level, "community")

    @patch("odoo.addons.energy_communities.models.res_users.ResUsers.make_ce_user")
    def test__add_company_managers(self, make_ce_user_mocked):
        new_company = self.create_company(
            "Community", "community", self.coordination.id
        )
        self.wizard.new_company_id = new_company

        self.wizard.add_company_managers()

        make_ce_user_mocked.assert_called_with(new_company, "role_ce_manager")

    def test__add_company_log(self):
        new_company = self.create_company(
            "Community", "community", self.coordination.id
        )
        self.wizard.new_company_id = new_company

        self.wizard.add_company_log()

        self.assertTrue(new_company.message_ids)
        expected_msg = '<p>Community created from: <a href="/web#id={}&amp;view_type=form&amp;model=crm.lead&amp;menu_id={}">{}</a></p>'.format(
            self.crm_lead.id, self.env.ref("crm.crm_menu_root").id, self.crm_lead.name
        )
        self.assertEqual(expected_msg, new_company.message_ids[0].body)
