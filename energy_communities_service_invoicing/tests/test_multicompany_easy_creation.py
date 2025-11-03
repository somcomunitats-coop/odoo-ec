from odoo import _
from odoo.tests import common, tagged

from odoo.addons.energy_communities.config import (
    CHART_OF_ACCOUNTS_GENERAL_CANARY_REF,
    CHART_OF_ACCOUNTS_GENERAL_REF,
    CHART_OF_ACCOUNTS_NON_PROFIT_CANARY_REF,
    CHART_OF_ACCOUNTS_NON_PROFIT_REF,
)
from odoo.addons.energy_communities.models.res_company import (
    _LEGAL_FORM_VALUES_NON_PROFIT,
)
from odoo.addons.energy_communities.utils import account_utils
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

CANARY_ACCOUNT_REF_100000 = "l10n_es_igic.{}_account_pymes_canary_100"
CANARY_ACCOUNT_REF_720000 = "l10n_es_igic.{}_account_assoc_canary_720"


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
        # execute async methods directly
        self.wizard_data_update = {
            "create_landing": False,
            "create_place": False,
            "create_user": False,
            "hook_cron": False,
        }
        self.coord_company = self.env.ref("energy_communities.coordinator_company_1")
        self.super_admin = self.browse_ref("base.user_admin")
        self.platform_admin = self.browse_ref(
            "energy_communities.res_users_admin_plataforma_demo"
        )
        self.coordinator_admin = self.browse_ref(
            "energy_communities.res_users_admin_coordinator_1_demo"
        )

    def test__company_cooperative_creation_ok_as_platform_admin_no_canary(self):
        self._test_company_creation_ok_case(
            self.platform_admin,
            self.coord_company,
            "energy_communities_crm.crm_lead_company_creation_demo_1",
            "coop",
        )

    def test__company_non_profit_without_recurring_creation_ok_as_platform_admin_no_canary(
        self,
    ):
        self._test_company_creation_ok_case(
            self.platform_admin,
            self.coord_company,
            "energy_communities_crm.crm_lead_company_creation_demo_2",
            "non_profit",
        )

    def test__company_non_profit_with_recurring_creation_ok_as_platform_admin_no_canary(
        self,
    ):
        self._test_company_creation_ok_case(
            self.platform_admin,
            self.coord_company,
            "energy_communities_crm.crm_lead_company_creation_demo_3",
            "non_profit_recurring",
        )

    def test__company_cooperative_creation_ok_as_platform_admin_canary(self):
        self._test_company_creation_ok_case(
            self.platform_admin,
            self.coord_company,
            "energy_communities_crm.crm_lead_company_creation_demo_4",
            "coop",
        )

    def test__company_non_profit_without_recurring_creation_ok_as_platform_admin_canary(
        self,
    ):
        self._test_company_creation_ok_case(
            self.platform_admin,
            self.coord_company,
            "energy_communities_crm.crm_lead_company_creation_demo_5",
            "non_profit",
        )

    def test__company_non_profit_with_recurring_creation_ok_as_platform_admin_canary(
        self,
    ):
        self._test_company_creation_ok_case(
            self.platform_admin,
            self.coord_company,
            "energy_communities_crm.crm_lead_company_creation_demo_6",
            "non_profit_recurring",
        )

    def test__company_cooperative_creation_ok_as_coord_admin_no_canary(self):
        self._test_company_creation_ok_case(
            self.coordinator_admin,
            self.coord_company,
            "energy_communities_crm.crm_lead_company_creation_demo_1",
            "coop",
        )

    def test__company_non_profit_without_recurring_creation_ok_as_coord_admin_no_canary(
        self,
    ):
        self._test_company_creation_ok_case(
            self.coordinator_admin,
            self.coord_company,
            "energy_communities_crm.crm_lead_company_creation_demo_2",
            "non_profit",
        )

    def test__company_non_profit_with_recurring_creation_ok_as_coord_admin_no_canary(
        self,
    ):
        self._test_company_creation_ok_case(
            self.coordinator_admin,
            self.coord_company,
            "energy_communities_crm.crm_lead_company_creation_demo_3",
            "non_profit_recurring",
        )

    def test__company_cooperative_creation_ok_as_coord_admin_canary(self):
        self._test_company_creation_ok_case(
            self.coordinator_admin,
            self.coord_company,
            "energy_communities_crm.crm_lead_company_creation_demo_4",
            "coop",
        )

    def test__company_non_profit_without_recurring_creation_ok_as_coord_admin_canary(
        self,
    ):
        self._test_company_creation_ok_case(
            self.coordinator_admin,
            self.coord_company,
            "energy_communities_crm.crm_lead_company_creation_demo_5",
            "non_profit",
        )

    def test__company_non_profit_with_recurring_creation_ok_as_coord_admin_canary(self):
        self._test_company_creation_ok_case(
            self.coordinator_admin,
            self.coord_company,
            "energy_communities_crm.crm_lead_company_creation_demo_6",
            "non_profit_recurring",
        )

    def _test_company_creation_ok_case(
        self,
        admin,
        context_company,
        crm_lead_ref,
        scenario_type,
    ):
        # we setup expected results and creation data

        # and setup the proper environment
        self.env = self.env(
            user=admin.id,
            context={"allowed_company_ids": [context_company.id]},
        )
        # given a lead
        creation_crm_lead = self.env.ref(crm_lead_ref)
        creation_data = creation_crm_lead._get_default_community_wizard()

        creation_data.update(self.wizard_data_update)
        # using mcec wizard to create a company
        creation_wizard = self.env["account.multicompany.easy.creation.wiz"].create(
            creation_data
        )

        # setup some expected results
        if scenario_type == "coop":
            if creation_wizard.is_canary():
                expected_account = CANARY_ACCOUNT_REF_100000
                expected_chart_of_accounts_ref = CHART_OF_ACCOUNTS_GENERAL_CANARY_REF
            else:
                expected_account = ACCOUNT_REF_100000
                expected_chart_of_accounts_ref = CHART_OF_ACCOUNTS_GENERAL_REF
        else:
            if creation_wizard.is_canary():
                expected_account = CANARY_ACCOUNT_REF_720000
                expected_chart_of_accounts_ref = CHART_OF_ACCOUNTS_NON_PROFIT_CANARY_REF
            else:
                expected_account = ACCOUNT_REF_720000
                expected_chart_of_accounts_ref = CHART_OF_ACCOUNTS_NON_PROFIT_REF

        result = creation_wizard.action_accept()

        # the wizard executes correctly
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["params"]["type"], "success")

        # and new data is correctly created
        self.env = self.env(user=self.env.ref("base.user_root").id)
        new_company = creation_wizard.new_company_id.sudo()
        self._assert__company_creation_relation_users_list(new_company)
        self._assert__wizard_creation_ok(
            creation_crm_lead,
            creation_wizard,
            context_company,
            new_company,
            expected_chart_of_accounts_ref,
        )
        self._assert__community_creation_ok(new_company)
        self._assert__comunity_creation_social_ok(new_company, creation_wizard)
        self._assert__users_and_partners_configuration_ok(new_company)
        self._assert__pricelist_configuration_ok(new_company)
        self._assert__coop_journal_and_accounts_ok(new_company, expected_account)
        self._assert__selfconsumption_journal_configuration_ok(new_company)

        self._assert__product_categs_saleteam_configuration_ok(new_company)
        self._assert__product_categs_journal_configuration_ok(new_company)

        if scenario_type == "coop":
            self._assert__vsir_journal_configuration_ok(new_company)
            self._assert__coop_product_configuration_ok(new_company)
            self._assert__vol_coop_product_configuration_ok(new_company)
        if scenario_type == "non_profit_recurring":
            self._assert__share_recurring_fee_product_configuration_ok(new_company)
        if scenario_type == "non_profit":
            self._assert__nonprofit_coop_product_configuration_ok(new_company)

        self._assert__bank_journals_configuration_ok(new_company)

    def _assert__bank_journals_configuration_ok(self, new_company):
        bank_journals = self.env["account.journal"].search(
            [("company_id", "=", new_company.id), ("type", "=", "bank")],
            order="id desc",
            limit=1,
        )
        with account_utils(self.env, use_sudo=True) as account_component:
            models_name = account_component.get_bank_journal_name(
                new_company.partner_id.bank_ids[
                    len(new_company.partner_id.bank_ids) - 1
                ]
            )
        self.assertEqual(len(bank_journals), 1)
        self.assertEqual(bank_journals.code, "BNK1")
        self.assertEqual(
            bank_journals.bank_account_id.partner_id.id, new_company.partner_id.id
        )
        self.assertEqual(bank_journals.name, models_name)
        self.assertEqual(bank_journals.default_account_id.name, models_name)

    def _assert__company_creation_relation_users_list(self, new_company):
        self.assertEqual(
            sorted(
                self.env[
                    "account.multicompany.easy.creation.wiz"
                ]._get_company_creation_related_users_list(new_company)
            ),
            sorted([user.id for user in self.expected_users]),
        )

    def _assert__wizard_creation_ok(
        self,
        creation_crm_lead,
        creation_wizard,
        context_company,
        new_company,
        expected_chart_of_accounts_ref,
    ):
        self.assertEqual(creation_wizard.parent_id, context_company)
        self.assertEqual(creation_wizard.crm_lead_id, creation_crm_lead)
        self.assertEqual(
            creation_wizard.chart_template_id,
            self.env.ref(expected_chart_of_accounts_ref),
        )

        if creation_wizard.is_canary():
            self.assertEqual(
                creation_wizard.default_sale_tax_id,
                self.env.ref("l10n_es_igic.account_tax_template_igic_r_7"),
            )
            self.assertEqual(
                creation_wizard.default_purchase_tax_id,
                self.env.ref("l10n_es_igic.account_tax_template_igic_sop_7"),
            )
        else:
            self.assertEqual(
                creation_wizard.default_sale_tax_id,
                self.env.ref("l10n_es.account_tax_template_s_iva21s"),
            )
            self.assertEqual(
                creation_wizard.default_purchase_tax_id,
                self.env.ref("l10n_es.account_tax_template_p_iva21_sc"),
            )
        self.assertFalse(creation_wizard.create_user)
        self.assertFalse(creation_wizard.creation_partner)

        self.assertEqual(
            creation_wizard.ce_member_status,
            creation_crm_lead.metadata_line_ids.filtered(
                lambda meta: meta.key == "ce_status"
            ).value,
        )

        ce_constitution_status = creation_crm_lead.metadata_line_ids.filtered(
            lambda meta: meta.key == "ce_constitution_status"
        ).value
        if ce_constitution_status == "constituted":
            self.assertEqual(
                creation_wizard.ce_status,
                "active",
            )
        else:
            self.assertEqual(
                creation_wizard.ce_status,
                "building",
            )

        # ASSERT: community creation wizard social data is correctly set
        self.assertEqual(
            creation_wizard.ce_twitter_url,
            creation_crm_lead.metadata_line_ids.filtered(
                lambda meta: meta.key == "ce_twitter_url"
            ).value,
        )
        self.assertEqual(
            creation_wizard.ce_telegram_url,
            creation_crm_lead.metadata_line_ids.filtered(
                lambda meta: meta.key == "ce_telegram_url"
            ).value,
        )
        self.assertEqual(
            creation_wizard.ce_instagram_url,
            creation_crm_lead.metadata_line_ids.filtered(
                lambda meta: meta.key == "ce_instagram_url"
            ).value,
        )
        self.assertEqual(
            creation_wizard.ce_facebook_url,
            creation_crm_lead.metadata_line_ids.filtered(
                lambda meta: meta.key == "ce_facebook_url"
            ).value,
        )
        self.assertEqual(
            creation_wizard.ce_mastodon_url,
            creation_crm_lead.metadata_line_ids.filtered(
                lambda meta: meta.key == "ce_mastodon_url"
            ).value,
        )
        self.assertEqual(
            creation_wizard.ce_bluesky_url,
            creation_crm_lead.metadata_line_ids.filtered(
                lambda meta: meta.key == "ce_bluesky_url"
            ).value,
        )

    def _assert__community_creation_ok(self, new_company):
        self.assertEqual(new_company.hierarchy_level, "community")
        # ASSERT: New companies has been created
        self.assertTrue(bool(new_company))
        self.assertEqual(new_company.tax_calculation_rounding_method, "round_globally")
        self.assertEqual(new_company.partner_id.lang, new_company.default_lang_id.code)

    def _assert__comunity_creation_social_ok(self, new_company, creation_wizard):
        self.assertEqual(new_company.social_twitter, creation_wizard.ce_twitter_url)
        self.assertEqual(new_company.social_telegram, creation_wizard.ce_telegram_url)
        self.assertEqual(new_company.social_instagram, creation_wizard.ce_instagram_url)
        self.assertEqual(new_company.social_facebook, creation_wizard.ce_facebook_url)
        self.assertEqual(new_company.social_mastodon, creation_wizard.ce_mastodon_url)
        self.assertEqual(new_company.social_bluesky, creation_wizard.ce_bluesky_url)

    def _assert__users_and_partners_configuration_ok(self, new_company):
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

    def _assert__pricelist_configuration_ok(self, new_company):
        created_pricelist = self.env["product.pricelist"].search(
            [("company_id", "=", new_company.id)]
        )
        self.assertEqual(len(created_pricelist), 1)
        self.assertEqual(new_company.pricelist_id, created_pricelist)

    def _assert__coop_journal_and_accounts_ok(self, new_company, expected_account_ref):
        coop_account = self.env.ref(expected_account_ref.format(new_company.id))
        self.assertTrue(bool(new_company.property_cooperator_account))
        self.assertTrue(bool(new_company.subscription_journal_id))
        self.assertEqual(new_company.subscription_journal_id.name, "Capital Social")
        self.assertEqual(new_company.subscription_journal_id.type, "sale")
        self.assertEqual(new_company.subscription_journal_id.company_id, new_company)
        self.assertEqual(new_company.subscription_journal_id.code, "CS")
        self.assertEqual(
            new_company.subscription_journal_id.default_account_id, coop_account
        )
        self.assertTrue(new_company.subscription_journal_id.refund_sequence)
        self.assertEqual(
            new_company.property_cooperator_account,
            self.env.ref(ACCOUNT_REF_440000.format(new_company.id)),
        )

    def _assert__selfconsumption_journal_configuration_ok(self, new_company):
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

    def _assert__vsir_journal_configuration_ok(self, new_company):
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

    def _assert__product_categs_saleteam_configuration_ok(self, new_company):
        self._assert_category_saleteam(new_company, COOP_SHARE_PRODUCT_CATEG_REF)
        self._assert_category_saleteam(
            new_company, COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF
        )
        self._assert_category_saleteam(
            new_company, COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF
        )
        self._assert_category_saleteam(new_company, PLATFORM_PACK_PRODUCT_CATEG_REF)
        self._assert_category_saleteam(
            new_company, RECURRING_FEE_PACK_PRODUCT_CATEG_REF
        )
        self._assert_category_saleteam(
            new_company, SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF
        )
        self._assert_category_saleteam(new_company, PLATFORM_SERVICE_PRODUCT_CATEG_REF)
        self._assert_category_saleteam(
            new_company, RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF
        )
        self._assert_category_saleteam(
            new_company, SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF
        )
        self._assert_category_saleteam(
            new_company, SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF
        )

    def _assert_category_saleteam(self, new_company, categ_ref):
        sale_team = (
            self.env.ref(categ_ref)
            .with_company(new_company)
            .service_invoicing_sale_team_id
        )
        self.assertTrue(bool(sale_team))
        self.assertEqual(sale_team.company_id, new_company)
        self.assertTrue(sale_team.is_default_team)
        self.assertEqual(sale_team.name, new_company.name)

    def _assert__product_categs_journal_configuration_ok(self, new_company):
        afc_journal = self.env["account.journal"].search(
            [("company_id", "=", new_company.id), ("code", "=", "AFC")], limit=1
        )
        self._assert_category_journal(new_company, COOP_SHARE_PRODUCT_CATEG_REF)
        self._assert_category_journal(
            new_company, COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF
        )
        self._assert_category_journal(
            new_company, COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF
        )
        self._assert_category_journal(new_company, PLATFORM_PACK_PRODUCT_CATEG_REF)
        self._assert_category_journal(new_company, RECURRING_FEE_PACK_PRODUCT_CATEG_REF)
        self._assert_category_journal(
            new_company, SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF, afc_journal
        )
        self._assert_category_journal(new_company, PLATFORM_SERVICE_PRODUCT_CATEG_REF)
        self._assert_category_journal(
            new_company, RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF
        )
        self.assertTrue(bool(new_company.subscription_journal_id))
        self._assert_category_journal(
            new_company,
            SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
            new_company.subscription_journal_id,
        )
        self._assert_category_journal(
            new_company, SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF, afc_journal
        )

    def _assert_category_journal(self, new_company, categ_ref, expected_journal=False):
        category = self.env.ref(categ_ref).with_company(new_company)
        if expected_journal:
            self.assertEqual(
                category.service_invoicing_sale_journal_id, expected_journal
            )
        else:
            self.assertEqual(
                category.service_invoicing_sale_journal_id, self.env["account.journal"]
            )

    def _assert__product_categs_accounts_configuration_ok_case(self, new_company):
        # given accounts
        account_empty = self.env["account.account"]
        account_100100 = self.env["account.account"].search(
            [("company_id", "=", new_company.id), ("code", "=", "100100")]
        )
        if new_company.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
            account_100000 = account_empty
            account_720000 = self.env.ref(ACCOUNT_REF_720000.format(new_company.id))
        else:
            account_100000 = self.env.ref(ACCOUNT_REF_100000.format(new_company.id))
            account_720000 = account_empty
        account_705000 = self.env.ref(ACCOUNT_REF_705000.format(new_company.id))
        account_607000 = self.env.ref(ACCOUNT_REF_607000.format(new_company.id))
        # assertions
        # coop share
        if new_company.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
            self._assert_category_accounts(
                new_company,
                COOP_SHARE_PRODUCT_CATEG_REF,
                account_720000,
                account_720000,
            )
        else:
            self._assert_category_accounts(
                new_company,
                COOP_SHARE_PRODUCT_CATEG_REF,
                account_100000,
                account_100000,
            )
        # coop voluntary share
        self._assert_category_accounts(
            new_company,
            COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF,
            account_100100,
            account_100100,
        )
        # platform pack
        self._assert_category_accounts(
            new_company, PLATFORM_PACK_PRODUCT_CATEG_REF, account_705000, account_607000
        )
        # platform service
        self._assert_category_accounts(
            new_company,
            PLATFORM_SERVICE_PRODUCT_CATEG_REF,
            account_705000,
            account_607000,
        )
        # share with recurring fee pack
        if new_company.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
            self._assert_category_accounts(
                new_company,
                COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
                account_720000,
                account_720000,
            )
        else:
            # categ = self.env.ref(COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF).with_company(company).property_account_income_categ_id
            self._assert_category_accounts(
                new_company,
                COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
                account_empty,
                account_empty,
            )
        # recurring fee pack
        self._assert_category_accounts(
            new_company,
            RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
            account_705000,
            account_607000,
        )
        # recurring fee service
        self._assert_category_accounts(
            new_company,
            RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
            account_705000,
            account_607000,
        )
        # share recurring fee service
        if new_company.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
            self._assert_category_accounts(
                new_company,
                SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
                account_720000,
                account_720000,
            )
        else:
            self._assert_category_accounts(
                new_company,
                SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
                account_705000,
                account_705000,
            )
        # selfconsumption pack
        self._assert_category_accounts(
            new_company,
            SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF,
            account_705000,
            account_607000,
        )
        # selfconsumption service
        self._assert_category_accounts(
            new_company,
            SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF,
            account_705000,
            account_607000,
        )

    def _assert_category_accounts(
        self, new_company, categ_ref, income_account, expense_account
    ):
        self.assertEqual(
            self.env.ref(categ_ref)
            .with_company(new_company)
            .property_account_income_categ_id,
            income_account,
        )
        self.assertEqual(
            self.env.ref(categ_ref)
            .with_company(new_company)
            .property_account_expense_categ_id,
            expense_account,
        )

    def _assert__coop_product_configuration_ok(self, new_company):
        self.assertTrue(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CSV"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CAAS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CIAS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CIA"),
                    ]
                )
            )
        )
        coop_product = self.env["product.template"].search(
            [("company_id", "=", new_company.id), ("default_code", "=", "CS")]
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
        self.assertEqual(coop_product.company_id, new_company)
        self.assertEqual(coop_product.short_name, "Capital social")
        self.assertTrue(coop_product.default_share_product)
        self.assertTrue(coop_product.by_company)
        self.assertTrue(coop_product.by_individual)
        self.assertEqual(coop_product.payment_mode_id, self.env["account.payment.mode"])
        self.assertFalse(coop_product.description_sale)

    def _assert__vol_coop_product_configuration_ok(self, new_company):
        self.assertTrue(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CAAS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CIAS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CIA"),
                    ]
                )
            )
        )
        coop_product = self.env["product.template"].search(
            [("company_id", "=", new_company.id), ("default_code", "=", "CSV")]
        )
        self.assertEqual(len(coop_product), 1)
        self.assertEqual(coop_product, new_company.voluntary_share_id)
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
        self.assertEqual(coop_product.company_id, new_company)
        self.assertEqual(coop_product.short_name, "Capital social voluntario")
        self.assertFalse(coop_product.default_share_product)
        self.assertTrue(coop_product.by_company)
        self.assertTrue(coop_product.by_individual)
        self.assertEqual(coop_product.payment_mode_id, self.env["account.payment.mode"])
        self.assertFalse(coop_product.description_sale)

    def _assert__share_recurring_fee_product_configuration_ok(self, new_company):
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CSV"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CIA"),
                    ]
                )
            )
        )
        coop_product = self.env["product.template"].search(
            [
                ("company_id", "=", new_company.id),
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
        self.assertEqual(coop_product.company_id, new_company)
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
        self.assertEqual(coop_product_contract_template.company_id, new_company)
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
        self.assertEqual(coop_contract_line_service.company_id, new_company)
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

    def _assert__nonprofit_coop_product_configuration_ok(self, new_company):
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CSV"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CAAS"),
                    ]
                )
            )
        )
        self.assertFalse(
            bool(
                self.env["product.template"].search(
                    [
                        ("company_id", "=", new_company.id),
                        ("default_code", "=", "CIAS"),
                    ]
                )
            )
        )
        coop_product = self.env["product.template"].search(
            [
                ("company_id", "=", new_company.id),
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
        self.assertEqual(coop_product.company_id, new_company)
        self.assertEqual(coop_product.short_name, "Cuota inicial afiliación")
        self.assertTrue(coop_product.default_share_product)
        self.assertTrue(coop_product.by_company)
        self.assertTrue(coop_product.by_individual)
        self.assertEqual(coop_product.payment_mode_id, self.env["account.payment.mode"])
        self.assertFalse(coop_product.description_sale)
