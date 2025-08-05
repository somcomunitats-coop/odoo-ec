from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestMultiCompanyEasyCreation(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
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
        creation_crm_lead = self.env.ref(
            "energy_communities_crm.crm_lead_company_creation_demo_1"
        )
        wizard = self._get_company_creation_wizard(creation_crm_lead)
        self.assertEqual(wizard.parent_id, self.coord_company)
        self.assertEqual(wizard.crm_lead_id, creation_crm_lead)
        self.assertEqual(
            wizard.chart_template_id,
            self.env.ref("l10n_es.account_chart_template_pymes"),
        )
        self.assertEqual(
            wizard.default_sale_tax_id,
            self.env.ref("l10n_es.account_tax_template_s_iva21s"),
        )
        self.assertEqual(
            wizard.default_purchase_tax_id,
            self.env.ref("l10n_es.account_tax_template_p_iva21_bc"),
        )
        self.assertFalse(wizard.create_user)
        self.assertFalse(wizard.creation_partner)
        creation_crm_lead = self.env.ref(
            "energy_communities_crm.crm_lead_company_creation_demo_2"
        )
        wizard = self._get_company_creation_wizard(creation_crm_lead)
        self.assertEqual(
            wizard.chart_template_id,
            self.env.ref("l10n_es.account_chart_template_assoc"),
        )

    def test__community_creation_ok(self):
        creation_crm_lead = self.env.ref(
            "energy_communities_crm.crm_lead_company_creation_demo_1"
        )
        wizard = self._get_company_creation_wizard(creation_crm_lead)
        wizard.action_accept()
        companies = self.env["res.company"].search(
            [("parent_id", "=", self.coord_company.id)]
        )
        # ASSERT: Now we have 3 communities
        self.assertEqual(len(companies), 3)
        for company in companies:
            self.assertEqual(company.hierarchy_level, "community")
        # ASSERT: New company has been created
        self.assertTrue(bool(wizard.new_company_id))

    def test__users_and_partners_configuration_ok(self):
        creation_crm_lead = self.env.ref(
            "energy_communities_crm.crm_lead_company_creation_demo_1"
        )
        wizard = self._get_company_creation_wizard(creation_crm_lead)
        wizard.action_accept()
        for user in self.expected_users:
            # ASSERT: community is defined on destination user company_ids
            self.assertTrue(
                bool(
                    user.company_ids.filtered(
                        lambda company: company.id == wizard.new_company_id.id
                    )
                )
            )
            # ASSERT: community is defined on destination user related partner company_ids
            self.assertTrue(
                bool(
                    user.partner_id.company_ids.filtered(
                        lambda company: company.id == wizard.new_company_id.id
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
                        and role_line.company_id.id == wizard.new_company_id.id
                    )
                )
            )
        )
        # ASSERT: new company related partner has new company assigned
        self.assertTrue(
            bool(
                wizard.new_company_id.partner_id.company_ids.filtered(
                    lambda company: company.id == wizard.new_company_id.id
                )
            )
        )
        # ASSERT: new company  related partner has platform company assigned
        self.assertTrue(
            bool(
                wizard.new_company_id.partner_id.company_ids.filtered(
                    lambda company: company.id == self.env.ref("base.main_company").id
                )
            )
        )
        # ASSERT: new company related partner has new company parent assigned
        self.assertTrue(
            bool(
                wizard.new_company_id.partner_id.company_ids.filtered(
                    lambda company: company.id == wizard.new_company_id.parent_id.id
                )
            )
        )
        # ASSERT: new company parent related partner has new company assigned
        self.assertTrue(
            bool(
                wizard.new_company_id.parent_id.partner_id.company_ids.filtered(
                    lambda company: company.id == wizard.new_company_id.id
                )
            )
        )

    def _get_company_creation_wizard(self, creation_crm_lead):
        data = creation_crm_lead._get_default_community_wizard()
        # avoid public data creation on testing
        data.update(
            {
                "create_landing": False,
                "create_place": False,
            }
        )
        return self.env["account.multicompany.easy.creation.wiz"].create(data)
