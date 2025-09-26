from odoo.tests import common, tagged

from odoo.addons.energy_communities.config import (
    CHART_OF_ACCOUNTS_GENERAL_REF,
    CHART_OF_ACCOUNTS_NON_PROFIT_REF,
)
from odoo.addons.energy_communities.models.res_company import (
    _LEGAL_FORM_VALUES_NON_PROFIT,
)
from odoo.addons.energy_communities_cooperator.config import (
    COOP_SHARE_PRODUCT_CATEG_REF,
    COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF,
)

from ..config import (
    COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
    PLATFORM_PACK_PRODUCT_CATEG_REF,
    PLATFORM_SERVICE_PRODUCT_CATEG_REF,
    RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
    RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
    SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF,
    SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF,
    SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
)

ACCOUNT_REF_100000 = "l10n_es.{}_account_pymes_100"
ACCOUNT_REF_720000 = "l10n_es.{}_account_assoc_720"
ACCOUNT_REF_705000 = "l10n_es.{}_account_common_7050"
ACCOUNT_REF_607000 = "l10n_es.{}_account_common_607"
ACCOUNT_REF_440000 = "l10n_es.{}_account_common_4400"
ACCOUNT_REF_662400 = "l10n_es.{}_account_common_6624"


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
            "create_user": False,
            "hook_cron": False,
        }
        # coop company
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

        # non_profit company (without recurring share)
        self.nonprofit_1_creation_crm_lead = self.env.ref(
            "energy_communities_crm.crm_lead_company_creation_demo_2"
        )
        creation_data = (
            self.nonprofit_1_creation_crm_lead._get_default_community_wizard()
        )
        creation_data.update(wizard_data_update)
        self.new_nonprofit_1_wizard = self.env[
            "account.multicompany.easy.creation.wiz"
        ].create(creation_data)
        self.new_nonprofit_1_wizard.action_accept()
        self.nonprofit_company_1 = self.new_nonprofit_1_wizard.new_company_id

        # non_profit company (with recurring fee)
        self.nonprofit_2_creation_crm_lead = self.env.ref(
            "energy_communities_crm.crm_lead_company_creation_demo_3"
        )
        creation_data = (
            self.nonprofit_2_creation_crm_lead._get_default_community_wizard()
        )
        wizard_data_update.update(
            {"fixed_invoicing_day": "01", "fixed_invoicing_month": "01"}
        )
        creation_data.update(wizard_data_update)
        self.new_nonprofit_2_wizard = self.env[
            "account.multicompany.easy.creation.wiz"
        ].create(creation_data)
        self.new_nonprofit_2_wizard.action_accept()
        self.nonprofit_company_2 = self.new_nonprofit_2_wizard.new_company_id

    def test__company_creation_relation_users_list(self):
        self.assertEqual(
            sorted(
                self.env[
                    "account.multicompany.easy.creation.wiz"
                ]._get_company_creation_related_users_list(self.coord_company)
            ),
            sorted([user.id for user in self.expected_users]),
        )
        self.assertEqual(
            sorted(
                self.env[
                    "account.multicompany.easy.creation.wiz"
                ]._get_company_creation_related_users_list(self.nonprofit_company_1)
            ),
            sorted([user.id for user in self.expected_users]),
        )
        self.assertEqual(
            sorted(
                self.env[
                    "account.multicompany.easy.creation.wiz"
                ]._get_company_creation_related_users_list(self.nonprofit_company_2)
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
            self.env.ref(CHART_OF_ACCOUNTS_GENERAL_REF),
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
            self.new_nonprofit_1_wizard.chart_template_id,
            self.env.ref(CHART_OF_ACCOUNTS_NON_PROFIT_REF),
        )
        self.assertEqual(
            self.new_nonprofit_2_wizard.chart_template_id,
            self.env.ref(CHART_OF_ACCOUNTS_NON_PROFIT_REF),
        )

    def test__community_creation_ok(self):
        companies = self.env["res.company"].search(
            [("parent_id", "=", self.coord_company.id)]
        )
        # ASSERT: Now we have 5 communities
        self.assertEqual(len(companies), 5)
        for company in companies:
            self.assertEqual(company.hierarchy_level, "community")
        # ASSERT: New companies has been created
        self.assertTrue(bool(self.coop_company))
        self.assertTrue(bool(self.nonprofit_company_1))
        self.assertTrue(bool(self.nonprofit_company_2))

    def test__users_and_partners_configuration_ok(self):
        self._test__users_and_partners_configuration_ok_case(self.coop_company)
        self._test__users_and_partners_configuration_ok_case(self.nonprofit_company_1)
        self._test__users_and_partners_configuration_ok_case(self.nonprofit_company_2)

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
            [("company_id", "=", self.nonprofit_company_1.id)]
        )
        self.assertEqual(len(created_pricelist), 1)
        self.assertEqual(self.nonprofit_company_1.pricelist_id, created_pricelist)

        created_pricelist = self.env["product.pricelist"].search(
            [("company_id", "=", self.nonprofit_company_2.id)]
        )
        self.assertEqual(len(created_pricelist), 1)
        self.assertEqual(self.nonprofit_company_2.pricelist_id, created_pricelist)

    def test__coop_journal_and_accounts_ok(self):
        self._test__coop_journal_and_accounts_ok_case(
            self.coop_company, ACCOUNT_REF_100000
        )
        self._test__coop_journal_and_accounts_ok_case(
            self.nonprofit_company_1, ACCOUNT_REF_720000
        )
        self._test__coop_journal_and_accounts_ok_case(
            self.nonprofit_company_2, ACCOUNT_REF_720000
        )

    def _test__coop_journal_and_accounts_ok_case(self, new_company, account_ref):
        coop_account = self.env.ref(account_ref.format(new_company.id))
        self.assertTrue(bool(new_company.property_cooperator_account))
        self.assertTrue(bool(new_company.subscription_journal_id))
        self.assertEqual(
            new_company.subscription_journal_id.name, "Subscription Journal"
        )
        self.assertEqual(new_company.subscription_journal_id.type, "sale")
        self.assertEqual(new_company.subscription_journal_id.company_id, new_company)
        self.assertEqual(new_company.subscription_journal_id.code, "SUBJ")
        self.assertEqual(
            new_company.subscription_journal_id.default_account_id, coop_account
        )
        self.assertTrue(new_company.subscription_journal_id.refund_sequence)
        self.assertEqual(
            new_company.property_cooperator_account,
            self.env.ref(ACCOUNT_REF_440000.format(new_company.id)),
        )

    def test__selfconsumption_journal_configuration_ok(self):
        self._test__selfconsumption_journal_configuration_ok_case(self.coop_company)
        self._test__selfconsumption_journal_configuration_ok_case(
            self.nonprofit_company_1
        )
        self._test__selfconsumption_journal_configuration_ok_case(
            self.nonprofit_company_2
        )

    def _test__selfconsumption_journal_configuration_ok_case(self, new_company):
        selconsumption_pack_categ = self.env.ref(SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF)
        selfconsumption_sale_journal = selconsumption_pack_categ.with_company(
            new_company
        ).service_invoicing_sale_journal_id
        selfconsumption_purchase_journal = selconsumption_pack_categ.with_company(
            new_company
        ).service_invoicing_purchase_journal_id
        self.assertTrue(bool(selfconsumption_sale_journal))
        self.assertFalse(bool(selfconsumption_purchase_journal))
        self.assertEqual(
            selfconsumption_sale_journal.name, "Autoconsumo Fotovoltaico Compartido"
        )
        self.assertEqual(selfconsumption_sale_journal.type, "sale")
        self.assertEqual(selfconsumption_sale_journal.company_id, new_company)
        self.assertEqual(selfconsumption_sale_journal.code, "AFC")
        self.assertEqual(
            selfconsumption_sale_journal.default_account_id,
            self.env.ref(ACCOUNT_REF_705000.format(new_company.id)),
        )
        self.assertTrue(selfconsumption_sale_journal.refund_sequence)

    def test__vsir_journal_configuration_ok_case(self):
        new_company = self.coop_company
        vsir_journal = new_company.voluntary_share_journal_account
        self.assertTrue(bool(vsir_journal))
        self.assertEqual(vsir_journal.name, "Intereses de aportaciones Voluntarias")
        self.assertEqual(vsir_journal.type, "purchase")
        self.assertEqual(vsir_journal.company_id, new_company)
        self.assertEqual(vsir_journal.code, "VSIR")
        self.assertEqual(
            vsir_journal.default_account_id,
            self.env.ref(ACCOUNT_REF_662400.format(new_company.id)),
        )
        self.assertTrue(vsir_journal.refund_sequence)

    def test__product_categs_configuration_ok(self):
        self._test__product_categs_saleteam_configuration_ok_case(self.coop_company)
        self._test__product_categs_saleteam_configuration_ok_case(
            self.nonprofit_company_1
        )
        self._test__product_categs_saleteam_configuration_ok_case(
            self.nonprofit_company_2
        )
        self._test__product_categs_journal_configuration_ok_case(self.coop_company)
        self._test__product_categs_journal_configuration_ok_case(
            self.nonprofit_company_1
        )
        self._test__product_categs_journal_configuration_ok_case(
            self.nonprofit_company_2
        )
        self._test__product_categs_accounts_configuration_ok_case(self.coop_company)
        self._test__product_categs_accounts_configuration_ok_case(
            self.nonprofit_company_1
        )
        self._test__product_categs_accounts_configuration_ok_case(
            self.nonprofit_company_2
        )

    def _test__product_categs_saleteam_configuration_ok_case(self, company):
        self._assert_category_saleteam(company, COOP_SHARE_PRODUCT_CATEG_REF)
        self._assert_category_saleteam(company, COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF)
        self._assert_category_saleteam(
            company, COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF
        )
        self._assert_category_saleteam(company, PLATFORM_PACK_PRODUCT_CATEG_REF)
        self._assert_category_saleteam(company, RECURRING_FEE_PACK_PRODUCT_CATEG_REF)
        self._assert_category_saleteam(company, SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF)
        self._assert_category_saleteam(company, PLATFORM_SERVICE_PRODUCT_CATEG_REF)
        self._assert_category_saleteam(company, RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF)
        self._assert_category_saleteam(
            company, SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF
        )
        self._assert_category_saleteam(
            company, SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF
        )

    def _assert_category_saleteam(self, company, categ_ref):
        sale_team = (
            self.env.ref(categ_ref).with_company(company).service_invoicing_sale_team_id
        )
        self.assertTrue(bool(sale_team))
        self.assertEqual(sale_team.company_id, company)
        self.assertTrue(sale_team.is_default_team)
        self.assertEqual(sale_team.name, company.name)

    def _test__product_categs_journal_configuration_ok_case(self, company):
        afc_journal = self.env["account.journal"].search(
            [("company_id", "=", company.id), ("code", "=", "AFC")], limit=1
        )
        self._assert_category_journal(company, COOP_SHARE_PRODUCT_CATEG_REF)
        self._assert_category_journal(company, COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF)
        self._assert_category_journal(
            company, COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF
        )
        self._assert_category_journal(company, PLATFORM_PACK_PRODUCT_CATEG_REF)
        self._assert_category_journal(company, RECURRING_FEE_PACK_PRODUCT_CATEG_REF)
        self._assert_category_journal(
            company, SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF, afc_journal
        )
        self._assert_category_journal(company, PLATFORM_SERVICE_PRODUCT_CATEG_REF)
        self._assert_category_journal(company, RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF)
        self.assertTrue(bool(company.subscription_journal_id))
        self._assert_category_journal(
            company,
            SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
            company.subscription_journal_id,
        )
        self._assert_category_journal(
            company, SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF, afc_journal
        )

    def _assert_category_journal(self, company, categ_ref, expected_journal=False):
        category = self.env.ref(categ_ref).with_company(company)
        if expected_journal:
            self.assertEqual(
                category.service_invoicing_sale_journal_id, expected_journal
            )
        else:
            self.assertEqual(
                category.service_invoicing_sale_journal_id, self.env["account.journal"]
            )

    def _test__product_categs_accounts_configuration_ok_case(self, company):
        # given accounts
        account_empty = self.env["account.account"]
        account_100100 = self.env["account.account"].search(
            [("company_id", "=", company.id), ("code", "=", "100100")]
        )
        if company.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
            account_100000 = account_empty
            account_720000 = self.env.ref(ACCOUNT_REF_720000.format(company.id))
        else:
            account_100000 = self.env.ref(ACCOUNT_REF_100000.format(company.id))
            account_720000 = account_empty
        account_705000 = self.env.ref(ACCOUNT_REF_705000.format(company.id))
        account_607000 = self.env.ref(ACCOUNT_REF_607000.format(company.id))
        # assertions
        # coop share
        if company.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
            self._assert_category_accounts(
                company, COOP_SHARE_PRODUCT_CATEG_REF, account_720000, account_720000
            )
        else:
            self._assert_category_accounts(
                company, COOP_SHARE_PRODUCT_CATEG_REF, account_100000, account_100000
            )
        # coop voluntary share
        self._assert_category_accounts(
            company,
            COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF,
            account_100100,
            account_100100,
        )
        # platform pack
        self._assert_category_accounts(
            company, PLATFORM_PACK_PRODUCT_CATEG_REF, account_705000, account_607000
        )
        # platform service
        self._assert_category_accounts(
            company, PLATFORM_SERVICE_PRODUCT_CATEG_REF, account_705000, account_607000
        )
        # share with recurring fee pack
        if company.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
            self._assert_category_accounts(
                company,
                COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
                account_720000,
                account_720000,
            )
        else:
            # categ = self.env.ref(COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF).with_company(company).property_account_income_categ_id
            self._assert_category_accounts(
                company,
                COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
                account_empty,
                account_empty,
            )
        # recurring fee pack
        self._assert_category_accounts(
            company,
            RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
            account_705000,
            account_607000,
        )
        # recurring fee service
        self._assert_category_accounts(
            company,
            RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
            account_705000,
            account_607000,
        )
        # share recurring fee service
        if company.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
            self._assert_category_accounts(
                company,
                SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
                account_720000,
                account_720000,
            )
        else:
            self._assert_category_accounts(
                company,
                SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
                account_705000,
                account_705000,
            )
        # selfconsumption pack
        self._assert_category_accounts(
            company,
            SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF,
            account_705000,
            account_607000,
        )
        # selfconsumption service
        self._assert_category_accounts(
            company,
            SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF,
            account_705000,
            account_607000,
        )

    def _assert_category_accounts(
        self, company, categ_ref, income_account, expense_account
    ):
        self.assertEqual(
            self.env.ref(categ_ref)
            .with_company(company)
            .property_account_income_categ_id,
            income_account,
        )
        self.assertEqual(
            self.env.ref(categ_ref)
            .with_company(company)
            .property_account_expense_categ_id,
            expense_account,
        )

    def test__products_configuration_ok(self):
        self._test__coop_product_configuration_ok()
        self._test__vol_coop_product_configuration_ok()
        self._test__share_recurring_fee_product_configuration_ok()
        self._test__nonprofit_coop_product_configuration_ok()

    def _test__coop_product_configuration_ok(self):
        self.assertTrue(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.coop_company.id),
                        ("default_code", "=", "CSV"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.coop_company.id),
                        ("default_code", "=", "CAAS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.coop_company.id),
                        ("default_code", "=", "CIAS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.coop_company.id),
                        ("default_code", "=", "CIA"),
                    ]
                )
            )
        )
        coop_product = self.env["product.template"].search(
            [("company_id", "=", self.coop_company.id), ("default_code", "=", "CS")]
        )
        self.assertEqual(len(coop_product), 1)
        self.assertEqual(coop_product.name, "Aportación obligatoria al capital social")
        self.assertEqual(
            coop_product.with_context(lang="ca_ES").name,
            "Aportació obligatòria al capital social",
        )
        self.assertEqual(
            coop_product.with_context(lang="es_ES").name,
            "Aportación obligatoria al capital social",
        )
        self.assertEqual(
            coop_product.with_context(lang="eu_ES").name,
            "Kapital sozialerako nahitaezko ekarpena",
        )
        self.assertFalse(coop_product.sale_ok)
        self.assertFalse(coop_product.purchase_ok)
        self.assertTrue(coop_product.is_share)
        self.assertTrue(coop_product.display_on_website)
        self.assertFalse(coop_product.is_contract)
        self.assertEqual(coop_product.detailed_type, "service")
        self.assertEqual(coop_product.invoice_policy, "order")
        self.assertEqual(coop_product.list_price, 130.0)
        self.assertEqual(coop_product.taxes_id, self.env["account.tax"])
        self.assertEqual(coop_product.default_code, "CS")
        self.assertEqual(coop_product.company_id, self.coop_company)
        self.assertEqual(coop_product.short_name, "Capital social")
        self.assertTrue(coop_product.default_share_product)
        self.assertTrue(coop_product.by_company)
        self.assertTrue(coop_product.by_individual)
        self.assertEqual(coop_product.payment_mode_id, self.env["account.payment.mode"])
        self.assertFalse(coop_product.description_sale)

    def _test__vol_coop_product_configuration_ok(self):
        self.assertTrue(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.coop_company.id),
                        ("default_code", "=", "CS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.coop_company.id),
                        ("default_code", "=", "CAAS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.coop_company.id),
                        ("default_code", "=", "CIAS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.coop_company.id),
                        ("default_code", "=", "CIA"),
                    ]
                )
            )
        )
        coop_product = self.env["product.template"].search(
            [("company_id", "=", self.coop_company.id), ("default_code", "=", "CSV")]
        )
        self.assertEqual(len(coop_product), 1)
        self.assertEqual(coop_product, self.coop_company.voluntary_share_id)
        self.assertEqual(coop_product.name, "Aportación voluntaria al capital social")
        self.assertEqual(
            coop_product.with_context(lang="ca_ES").name,
            "Aportació voluntària al capital social",
        )
        self.assertEqual(
            coop_product.with_context(lang="es_ES").name,
            "Aportación voluntaria al capital social",
        )
        self.assertEqual(
            coop_product.with_context(lang="eu_ES").name,
            "Kapital sozialerako borondatezko ekarpena",
        )
        self.assertFalse(coop_product.sale_ok)
        self.assertFalse(coop_product.purchase_ok)
        self.assertTrue(coop_product.is_share)
        self.assertTrue(coop_product.display_on_website)
        self.assertFalse(coop_product.is_contract)
        self.assertEqual(coop_product.detailed_type, "service")
        self.assertEqual(coop_product.invoice_policy, "order")
        self.assertEqual(coop_product.list_price, 10.0)
        self.assertEqual(coop_product.taxes_id, self.env["account.tax"])
        self.assertEqual(coop_product.default_code, "CSV")
        self.assertEqual(coop_product.company_id, self.coop_company)
        self.assertEqual(coop_product.short_name, "Capital social voluntario")
        self.assertFalse(coop_product.default_share_product)
        self.assertTrue(coop_product.by_company)
        self.assertTrue(coop_product.by_individual)
        self.assertEqual(coop_product.payment_mode_id, self.env["account.payment.mode"])
        self.assertFalse(coop_product.description_sale)

    def _test__share_recurring_fee_product_configuration_ok(self):
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.nonprofit_company_2.id),
                        ("default_code", "=", "CSV"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.nonprofit_company_2.id),
                        ("default_code", "=", "CS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.nonprofit_company_2.id),
                        ("default_code", "=", "CIA"),
                    ]
                )
            )
        )
        coop_product = self.env["product.template"].search(
            [
                ("company_id", "=", self.nonprofit_company_2.id),
                ("default_code", "=", "CIAS"),
            ]
        )
        self.assertEqual(len(coop_product), 1)
        self.assertEqual(coop_product.name, "Cuota inicial afiliación socia")
        self.assertEqual(
            coop_product.with_context(lang="ca_ES").name,
            "Cuota inicial afiliació sòcia",
        )
        self.assertEqual(
            coop_product.with_context(lang="es_ES").name,
            "Cuota inicial afiliación socia",
        )
        self.assertEqual(
            coop_product.with_context(lang="eu_ES").name,
            "Bazkide afiliazioaren hasierako kuota",
        )
        self.assertTrue(coop_product.sale_ok)
        self.assertTrue(coop_product.purchase_ok)
        self.assertTrue(coop_product.is_share)
        self.assertTrue(coop_product.display_on_website)
        self.assertTrue(coop_product.is_contract)
        self.assertEqual(coop_product.detailed_type, "service")
        self.assertEqual(coop_product.invoice_policy, "order")
        self.assertEqual(coop_product.list_price, 50.0)
        self.assertEqual(coop_product.taxes_id, self.env["account.tax"])
        self.assertEqual(coop_product.default_code, "CIAS")
        self.assertEqual(coop_product.company_id, self.nonprofit_company_2)
        self.assertEqual(coop_product.short_name, "Cuota inicial afiliación")
        self.assertTrue(coop_product.default_share_product)
        self.assertTrue(coop_product.by_company)
        self.assertTrue(coop_product.by_individual)
        self.assertEqual(coop_product.payment_mode_id, self.env["account.payment.mode"])
        self.assertEqual(
            coop_product.description_sale, "Cuota inicial afiliación socia"
        )
        self.assertEqual(
            coop_product.with_context(lang="ca_ES").description_sale,
            "Cuota inicial afiliació sòcia",
        )
        self.assertEqual(
            coop_product.with_context(lang="es_ES").description_sale,
            "Cuota inicial afiliación socia",
        )
        self.assertEqual(
            coop_product.with_context(lang="eu_ES").description_sale,
            "Bazkide afiliazioaren hasierako kuota",
        )
        coop_product_contract_template = coop_product.property_contract_template_id
        self.assertTrue(bool(coop_product_contract_template))
        self.assertEqual(coop_product_contract_template.contract_type, "sale")
        self.assertEqual(
            coop_product_contract_template.pack_type, "share_recurring_fee_pack"
        )
        self.assertFalse(coop_product_contract_template.is_free_pack)
        self.assertEqual(
            coop_product_contract_template.company_id, self.nonprofit_company_2
        )
        self.assertEqual(len(coop_product_contract_template.contract_line_ids), 1)
        coop_contract_line = coop_product_contract_template.contract_line_ids[0]
        coop_contract_line_service = coop_product_contract_template.contract_line_ids[
            0
        ].product_id
        self.assertEqual(
            coop_contract_line_service.name, "Cuota anual afiliación socia"
        )
        self.assertEqual(
            coop_contract_line_service.with_context(lang="ca_ES").name,
            "Cuota annual afiliació sòcia",
        )
        self.assertEqual(
            coop_contract_line_service.with_context(lang="es_ES").name,
            "Cuota anual afiliación socia",
        )
        self.assertEqual(
            coop_contract_line_service.with_context(lang="eu_ES").name,
            "Bazkide afiliazioaren urteko kuota",
        )
        self.assertTrue(coop_contract_line_service.sale_ok)
        self.assertTrue(coop_contract_line_service.purchase_ok)
        self.assertFalse(coop_contract_line_service.is_share)
        self.assertFalse(coop_contract_line_service.display_on_website)
        self.assertFalse(coop_contract_line_service.is_contract)
        self.assertEqual(coop_contract_line_service.detailed_type, "service")
        self.assertEqual(coop_contract_line_service.invoice_policy, "order")
        self.assertEqual(coop_contract_line_service.list_price, 50.0)
        self.assertEqual(coop_contract_line_service.taxes_id, self.env["account.tax"])
        self.assertEqual(coop_contract_line_service.default_code, "CAAS")
        self.assertEqual(
            coop_contract_line_service.company_id, self.nonprofit_company_2
        )
        self.assertEqual(
            coop_contract_line_service.short_name, "Cuota anual afiliación"
        )
        self.assertFalse(coop_contract_line_service.default_share_product)
        self.assertFalse(coop_contract_line_service.by_company)
        self.assertFalse(coop_contract_line_service.by_individual)
        self.assertEqual(
            coop_contract_line_service.payment_mode_id, self.env["account.payment.mode"]
        )
        self.assertEqual(
            coop_contract_line_service.description_sale, "Cuota anual afiliación"
        )
        self.assertEqual(
            coop_contract_line_service.with_context(lang="ca_ES").description_sale,
            "Cuota annual afiliació sòcia",
        )
        self.assertEqual(
            coop_contract_line_service.with_context(lang="es_ES").description_sale,
            "Cuota anual afiliación socia",
        )
        self.assertEqual(
            coop_contract_line_service.with_context(lang="eu_ES").description_sale,
            "Bazkide afiliazioaren urteko kuota",
        )

    def _test__nonprofit_coop_product_configuration_ok(self):
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.nonprofit_company_1.id),
                        ("default_code", "=", "CS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.nonprofit_company_1.id),
                        ("default_code", "=", "CSV"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.nonprofit_company_1.id),
                        ("default_code", "=", "CAAS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", self.nonprofit_company_1.id),
                        ("default_code", "=", "CIAS"),
                    ]
                )
            )
        )
        coop_product = self.env["product.template"].search(
            [
                ("company_id", "=", self.nonprofit_company_1.id),
                ("default_code", "=", "CIA"),
            ]
        )
        self.assertEqual(len(coop_product), 1)
        self.assertEqual(coop_product.name, "Cuota inicial afiliación socia")
        self.assertEqual(
            coop_product.with_context(lang="ca_ES").name,
            "Cuota inicial afiliació sòcia",
        )
        self.assertEqual(
            coop_product.with_context(lang="es_ES").name,
            "Cuota inicial afiliación socia",
        )
        self.assertEqual(
            coop_product.with_context(lang="eu_ES").name,
            "Bazkide afiliazioaren hasierako kuota",
        )
        self.assertFalse(coop_product.sale_ok)
        self.assertFalse(coop_product.purchase_ok)
        self.assertTrue(coop_product.is_share)
        self.assertTrue(coop_product.display_on_website)
        self.assertFalse(coop_product.is_contract)
        self.assertEqual(coop_product.detailed_type, "service")
        self.assertEqual(coop_product.invoice_policy, "order")
        self.assertEqual(coop_product.list_price, 90.0)
        self.assertEqual(coop_product.taxes_id, self.env["account.tax"])
        self.assertEqual(coop_product.default_code, "CIA")
        self.assertEqual(coop_product.company_id, self.nonprofit_company_1)
        self.assertEqual(coop_product.short_name, "Cuota inicial afiliación")
        self.assertTrue(coop_product.default_share_product)
        self.assertTrue(coop_product.by_company)
        self.assertTrue(coop_product.by_individual)
        self.assertEqual(coop_product.payment_mode_id, self.env["account.payment.mode"])
        self.assertFalse(coop_product.description_sale)
