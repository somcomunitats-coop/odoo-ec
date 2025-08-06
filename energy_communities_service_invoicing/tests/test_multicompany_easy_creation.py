from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestMultiCompanyEasyCreation(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.expected_users = [
            # coordinator admins from coordinator company
            self.env.ref("energy_communities.res_users_admin_coordinator_1_demo"),
            # platform admins
            self.env.ref("base.user_admin"),
            self.env.ref("energy_communities.res_users_admin_plataforma_demo"),
            # public users
            self.env.ref("base.public_user"),
        ]
        self.coord_company = self.env.ref("energy_communities.coordinator_company_1")
        # avoid public data creation on testing
        # execute async methods directly
        wizard_data_update = {
            "create_landing": False,
            "create_place": False,
            "hook_cron": False,
        }
        self.cooperative_creation_crm_lead = self.env.ref(
            "energy_communities_crm.crm_lead_company_creation_demo_1"
        )
        creation_data = (
            self.cooperative_creation_crm_lead._get_default_community_wizard()
        )
        creation_data.update(wizard_data_update)
        self.new_cooperative_wizard = self.env[
            "account.multicompany.easy.creation.wiz"
        ].create(creation_data)
        self.new_cooperative_wizard.action_accept()
        self.coop_company = self.new_cooperative_wizard.new_company_id
        self.nonprofit_creation_crm_lead = self.env.ref(
            "energy_communities_crm.crm_lead_company_creation_demo_2"
        )
        creation_data = self.nonprofit_creation_crm_lead._get_default_community_wizard()
        creation_data.update(wizard_data_update)
        self.new_nonprofit_wizard = self.env[
            "account.multicompany.easy.creation.wiz"
        ].create(creation_data)
        self.new_nonprofit_wizard.action_accept()
        self.nonprofit_company = self.new_nonprofit_wizard.new_company_id

    def test__company_creation_relation_users_list(self):
        self.assertEqual(
            sorted(
                self.env[
                    "account.multicompany.easy.creation.wiz"
                ]._get_company_creation_related_users_list(self.coord_company)
            ),
            sorted([user.id for user in self.expected_users]),
        )

    def test__wizard_creation_ok(self):
        self.assertEqual(self.new_cooperative_wizard.parent_id, self.coord_company)
        self.assertEqual(
            self.new_cooperative_wizard.crm_lead_id, self.cooperative_creation_crm_lead
        )
        self.assertEqual(
            self.new_cooperative_wizard.chart_template_id,
            self.env.ref("l10n_es.account_chart_template_pymes"),
        )
        self.assertEqual(
            self.new_cooperative_wizard.default_sale_tax_id,
            self.env.ref("l10n_es.account_tax_template_s_iva21s"),
        )
        self.assertEqual(
            self.new_cooperative_wizard.default_purchase_tax_id,
            self.env.ref("l10n_es.account_tax_template_p_iva21_bc"),
        )
        self.assertFalse(self.new_cooperative_wizard.create_user)
        self.assertFalse(self.new_cooperative_wizard.creation_partner)
        self.assertEqual(
            self.new_nonprofit_wizard.chart_template_id,
            self.env.ref("l10n_es.account_chart_template_assoc"),
        )

    def test__community_creation_ok(self):
        companies = self.env["res.company"].search(
            [("parent_id", "=", self.coord_company.id)]
        )
        # ASSERT: Now we have 4 communities
        self.assertEqual(len(companies), 4)
        for company in companies:
            self.assertEqual(company.hierarchy_level, "community")
        # ASSERT: New companies has been created
        self.assertTrue(bool(self.coop_company))
        self.assertTrue(bool(self.nonprofit_company))

    def test__users_and_partners_configuration_ok(self):
        self._test__users_and_partners_configuration_ok_case(self.coop_company)
        self._test__users_and_partners_configuration_ok_case(self.nonprofit_company)

    def _test__users_and_partners_configuration_ok_case(self, new_company):
        for user in self.expected_users:
            # ASSERT: community is defined on destination user company_ids
            self.assertTrue(
                bool(
                    user.company_ids.filtered(
                        lambda company: company.id == new_company.id
                    )
                )
            )
            # ASSERT: community is defined on destination user related partner company_ids
            self.assertTrue(
                bool(
                    user.partner_id.company_ids.filtered(
                        lambda company: company.id == new_company.id
                    )
                )
            )
        # ASSERT: destination coordinator users are a community manager of the community
        self.assertTrue(
            bool(
                self.expected_users[0].role_line_ids.filtered(
                    lambda role_line: (
                        role_line.role_id.id
                        == self.env.ref("energy_communities.role_ce_manager").id
                        and role_line.company_id.id == new_company.id
                    )
                )
            )
        )
        # ASSERT: new company related partner has new company assigned
        self.assertTrue(
            bool(
                new_company.partner_id.company_ids.filtered(
                    lambda company: company.id == new_company.id
                )
            )
        )
        # ASSERT: new company  related partner has platform company assigned
        self.assertTrue(
            bool(
                new_company.partner_id.company_ids.filtered(
                    lambda company: company.id == self.env.ref("base.main_company").id
                )
            )
        )
        # ASSERT: new company related partner has new company parent assigned
        self.assertTrue(
            bool(
                new_company.partner_id.company_ids.filtered(
                    lambda company: company.id == new_company.parent_id.id
                )
            )
        )
        # ASSERT: new company parent related partner has new company assigned
        self.assertTrue(
            bool(
                new_company.parent_id.partner_id.company_ids.filtered(
                    lambda company: company.id == new_company.id
                )
            )
        )

    def test__pricelist_configuration_ok(self):
        created_pricelist = self.env["product.pricelist"].search(
            [("company_id", "=", self.coop_company.id)]
        )
        self.assertEqual(len(created_pricelist), 1)
        self.assertEqual(self.coop_company.pricelist_id, created_pricelist)
        created_pricelist = self.env["product.pricelist"].search(
            [("company_id", "=", self.nonprofit_company.id)]
        )
        self.assertEqual(len(created_pricelist), 1)
        self.assertEqual(self.nonprofit_company.pricelist_id, created_pricelist)
