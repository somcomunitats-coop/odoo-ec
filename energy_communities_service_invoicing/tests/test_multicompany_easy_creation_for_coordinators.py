from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestMultiCompanyEasyCreationForCoordinators(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        # execute async methods directly
        self.wizard_data_update = {
            "create_landing": False,
            "create_place": False,
            "create_user": False,
            "hook_cron": False,
        }
        self.coord_company = self.env.ref("energy_communities.coordinator_company_1")
        self.platform_admin = self.browse_ref(
            "energy_communities.res_users_admin_plataforma_demo"
        )
        self.coordinator_admin = self.browse_ref(
            "energy_communities.res_users_admin_coordinator_1_demo"
        )

    def test__company_cooperative_creation_ok_as_platform_admin(self):
        self._test_company_creation_ok_case(
            self.platform_admin,
            "energy_communities_crm.crm_lead_company_creation_demo_1",
        )

    def test__company_non_profit_without_recurring_creation_ok_as_platform_admin(self):
        self._test_company_creation_ok_case(
            self.platform_admin,
            "energy_communities_crm.crm_lead_company_creation_demo_2",
        )

    def test__company_non_profit_with_recurring_creation_ok_as_platform_admin(self):
        self._test_company_creation_ok_case(
            self.platform_admin,
            "energy_communities_crm.crm_lead_company_creation_demo_3",
            {"fixed_invoicing_day": "01", "fixed_invoicing_month": "01"},
        )

    def test__company_cooperative_creation_ok_as_coord_admin(self):
        self._test_company_creation_ok_case(
            self.coordinator_admin,
            "energy_communities_crm.crm_lead_company_creation_demo_1",
        )

    def test__company_non_profit_without_recurring_creation_ok_as_coord_admin(self):
        self._test_company_creation_ok_case(
            self.coordinator_admin,
            "energy_communities_crm.crm_lead_company_creation_demo_2",
        )

    def test__company_non_profit_with_recurring_creation_ok_as_coord_admin(self):
        self._test_company_creation_ok_case(
            self.coordinator_admin,
            "energy_communities_crm.crm_lead_company_creation_demo_3",
            {"fixed_invoicing_day": "01", "fixed_invoicing_month": "01"},
        )

    def _test_company_creation_ok_case(
        self, admin, crm_lead_ref, wizard_data_update_custom=False
    ):
        # and the proper environment
        self.env = self.env(
            user=admin.id,
            context={"allowed_company_ids": [self.coord_company.id]},
        )
        creation_crm_lead = self.env.ref(crm_lead_ref)
        creation_data = creation_crm_lead._get_default_community_wizard()
        if wizard_data_update_custom:
            self.wizard_data_update.update(wizard_data_update_custom)
        creation_data.update(self.wizard_data_update)
        creation_wizard = self.env["account.multicompany.easy.creation.wiz"].create(
            creation_data
        )
        result = creation_wizard.action_accept()
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["params"]["type"], "success")
