from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.config import (
    PACK_TYPE_NONE,
    PACK_TYPE_PLATFORM,
    PACK_TYPE_RECURRING_FEE,
    PACK_TYPE_SELFCONSUMPTION,
    PACK_TYPE_SHARE_RECURRING_FEE,
)

from .service_invoicing_testing_product_creator import (
    ServiceInvoicingTestingProductCreator,
)
from .testing_cases import _PRODUCT_UTILS_TESTING_CASES


@tagged("-at_install", "post_install")
class TestPackTypeMixin(TransactionCase, ServiceInvoicingTestingProductCreator):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_invoice_pack_type_case_0(self):
        # Given a demo invoice not pack generated
        invoice = self.env.ref("account.1_demo_invoice_3")
        self.assertEqual(invoice.pack_type, PACK_TYPE_NONE)

    def test_contract_pack_type_case_0(self):
        new_contract = self.env["contract.contract"].create(
            {
                "name": "Manual Test Contract",
                "partner_id": self.env.ref("base.res_partner_4").id,
                "journal_id": 1,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.assertEqual(new_contract.pack_type, PACK_TYPE_NONE)

    def test_pack_type_case_1(self):
        pack_product = self._create_pack_product(
            _PRODUCT_UTILS_TESTING_CASES["interval_prepaid_platform"]
        )
        self._assert_pack_type_consistency_on_pack_creation(
            pack_product, PACK_TYPE_PLATFORM
        )
        partner = self.env["res.partner"].search(
            [("name", "=", "Community 1")], limit=1
        )
        related_contract = self._assign_pack_to_partner(pack_product, partner)
        self._assert_pack_type_consistency_on_contract_creation(
            related_contract, PACK_TYPE_PLATFORM
        )

    def test_pack_type_case_2(self):
        pack_product = self._create_pack_product(
            _PRODUCT_UTILS_TESTING_CASES["fixed_prepaid_recurring_fee"]
        )
        self._assert_pack_type_consistency_on_pack_creation(
            pack_product, PACK_TYPE_RECURRING_FEE
        )
        partner = self._get_cooperative_partner(pack_product.company_id.id)
        related_contract = self._assign_pack_to_partner(pack_product, partner)
        self._assert_pack_type_consistency_on_contract_creation(
            related_contract, PACK_TYPE_RECURRING_FEE
        )

    def test_pack_type_case_3(self):
        pack_product = self._create_pack_product(
            _PRODUCT_UTILS_TESTING_CASES["fixed_prepaid_share_recurring_fee"]
        )
        self._assert_pack_type_consistency_on_pack_creation(
            pack_product, PACK_TYPE_SHARE_RECURRING_FEE
        )
        partner = self._get_cooperative_partner(pack_product.company_id.id)
        related_contract = self._assign_pack_to_partner(pack_product, partner)
        self._assert_pack_type_consistency_on_contract_creation(
            related_contract, PACK_TYPE_SHARE_RECURRING_FEE
        )

    def test_pack_type_case_4(self):
        pack_product = self._create_pack_product(
            _PRODUCT_UTILS_TESTING_CASES["interval_prepaid_selfconsumption"]
        )
        self._assert_pack_type_consistency_on_pack_creation(
            pack_product, PACK_TYPE_SELFCONSUMPTION
        )
        partner = self._get_cooperative_partner(pack_product.company_id.id)
        related_contract = self._assign_pack_to_partner(pack_product, partner)
        self._assert_pack_type_consistency_on_contract_creation(
            related_contract, PACK_TYPE_SELFCONSUMPTION
        )

    def _get_cooperative_partner(self, company_id_id):
        sr = self.env["subscription.request"].search(
            [("company_id", "=", company_id_id)], limit=1
        )
        if sr.state == "draft":
            sr.validate_subscription_request_with_company()
        return sr.partner_id

    def _assert_pack_type_consistency_on_pack_creation(
        self, pack_product, expected_pack_type
    ):
        self.assertEqual(pack_product.pack_type, expected_pack_type)
        self.assertEqual(
            pack_product.property_contract_template_id.pack_type, expected_pack_type
        )
        self.assertEqual(pack_product.categ_id.pack_type, expected_pack_type)

    def _assert_pack_type_consistency_on_contract_creation(
        self, related_contract, expected_pack_type
    ):
        self.assertEqual(related_contract.pack_type, expected_pack_type)
        related_contract.recurring_create_invoice()
        new_invoice = related_contract._get_related_invoices()
        self.assertEqual(new_invoice.pack_type, expected_pack_type)
