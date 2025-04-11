from datetime import datetime

from faker import Faker

from odoo.tests import common, tagged

faker = Faker(locale="es_ES")


@tagged("-at_install", "post_install")
class TestMultiCompanyEasyCreation(common.TransactionCase):
    # TODO: Move to demo data
    def create_crm_lead(self):
        # related_team = self.env["crm.team"].search([("company_id","=",self.coordinator_company.id)])
        return self.env["crm.lead"].create(
            {
                "name": "Community 3",
                "email_from": faker.email(),
                "submission_type": "place_submission",
                "company_id": self.coordinator_company.id,
                # "team_id": related_team[0].id,
                "source_id": self.env.ref(
                    "energy_communities.ce_source_creation_ce_proposal"
                ).id,
                "metadata_line_ids": [
                    (0, 0, {"key": "ce_name", "value": "Community 3"}),
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
        self.maxDiff = None
        self.coordinator_company = self.env.ref(
            "energy_communities.coordinator_company_1"
        )
        self.crm_lead = self.create_crm_lead()
        wizard_params = self.crm_lead._get_default_community_wizard()
        # disable landing and map place creation
        wizard_params["create_landing"] = False
        wizard_params["create_place"] = False
        # TODO: Test landing and map place creation on a different space
        self.wizard = self.env["account.multicompany.easy.creation.wiz"].create(
            wizard_params
        )
        self.expected_users = [
            # coordinator admins from coordinator company
            self.env.ref("energy_communities.res_users_admin_coordinator_1_demo"),
            # platform admins
            self.env.ref("base.user_admin"),
            self.env.ref("energy_communities.res_users_admin_plataforma_demo"),
            # public users
            self.env.ref("base.public_user"),
        ]

    def test__company_creation_relation_users_list(self):
        self.assertEqual(
            sorted(
                self.env[
                    "account.multicompany.easy.creation.wiz"
                ]._get_company_creation_related_users_list(self.coordinator_company)
            ),
            sorted([user.id for user in self.expected_users]),
        )

    def test__get_default_community_wizard(self):
        self.assertEqual(
            self.crm_lead._get_default_community_wizard(),
            {
                "name": self.crm_lead.name,
                "legal_name": self.crm_lead.name,
                "city": "Girona",
                "email": "random@somcomunitats.coop",
                "foundation_date": datetime.strptime("1994-09-01", "%Y-%m-%d"),
                "parent_id": self.coordinator_company.id,
                "crm_lead_id": self.crm_lead.id,
                "phone": "666666666",
                "street": "Av St Narcís",
                "vat": "38948723V",
                "zip_code": "17005",
                "user_ids": self.env[
                    "account.multicompany.easy.creation.wiz"
                ]._get_company_creation_related_users_list(self.coordinator_company),
                "chart_template_id": self.env.ref(
                    "l10n_es.account_chart_template_pymes"
                ).id,
                "update_default_taxes": True,
                "default_sale_tax_id": self.env.ref(
                    "l10n_es.account_tax_template_s_iva21s"
                ).id,
                "default_purchase_tax_id": self.env.ref(
                    "l10n_es.account_tax_template_p_iva21_bc"
                ).id,
                "property_cooperator_account": self.env.ref(
                    "l10n_es.{}_account_common_4400".format(
                        str(self.coordinator_company.id)
                    )
                ).id,
                "product_share_template": self.env.ref(
                    "energy_communities_cooperator.coordinator_company_1_share_type_demo"
                ).id,
                "create_user": False,
                "create_landing": True,
                "create_place": True,
                "creation_partner": False,
            },
        )

    def test__action_accept(self):
        self.wizard.action_accept()
        companies = self.env["res.company"].search(
            [("parent_id", "=", self.coordinator_company.id)]
        )
        # WORKFLOW: Company creation successful
        # CHECK: Now we have 3 communities
        self.assertEqual(len(companies), 3)
        for company in companies:
            self.assertEqual(company.hierarchy_level, "community")
        # CHECK: New company has been created
        self.assertTrue(bool(self.wizard.new_company_id))
        # CHECK: Message on new company logger
        self.assertEqual(
            '<p>Community created from: <a href="/web#id={}&amp;view_type=form&amp;model=crm.lead&amp;menu_id={}">{}</a></p>'.format(
                self.crm_lead.id,
                self.env.ref("crm.crm_menu_root").id,
                self.crm_lead.name,
            ),
            self.wizard.new_company_id.message_ids[0].body,
        )
        # WORKFLOW: Wizard related users properly configured
        for user in self.expected_users:
            # CHECK: community is defined on destination user company_ids
            self.assertTrue(
                bool(
                    user.company_ids.filtered(
                        lambda company: company.id == self.wizard.new_company_id.id
                    )
                )
            )
            # CHECK: community is defined on destination user related partner company_ids
            self.assertTrue(
                bool(
                    user.partner_id.company_ids.filtered(
                        lambda company: company.id == self.wizard.new_company_id.id
                    )
                )
            )
        # CHECK: destination coordinator users are a community manager of the community
        self.assertTrue(
            bool(
                self.expected_users[0].role_line_ids.filtered(
                    lambda role_line: (
                        role_line.role_id.id
                        == self.env.ref("energy_communities.role_ce_manager").id
                        and role_line.company_id.id == self.wizard.new_company_id.id
                    )
                )
            )
        )
        # WORKFLOW: new company and it's hierarchy companies related partners properly configured
        # CHECK: new company related partner has new company assigned
        self.assertTrue(
            bool(
                self.wizard.new_company_id.partner_id.company_ids.filtered(
                    lambda company: company.id == self.wizard.new_company_id.id
                )
            )
        )
        # CHECK: new company  related partner has platform company assigned
        self.assertTrue(
            bool(
                self.wizard.new_company_id.partner_id.company_ids.filtered(
                    lambda company: company.id == self.env.ref("base.main_company").id
                )
            )
        )
        # CHECK: new company related partner has new company parent assigned
        self.assertTrue(
            bool(
                self.wizard.new_company_id.partner_id.company_ids.filtered(
                    lambda company: company.id
                    == self.wizard.new_company_id.parent_id.id
                )
            )
        )
        # CHECK: new company parent related partner has new company assigned
        self.assertTrue(
            bool(
                self.wizard.new_company_id.parent_id.partner_id.company_ids.filtered(
                    lambda company: company.id == self.wizard.new_company_id.id
                )
            )
        )
