from dateutil.relativedelta import relativedelta

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.config import PACK_TYPE_PLATFORM
from odoo.addons.energy_communities.utils import contract_utils

from .service_invoicing_testing_contract_creator import (
    ServiceInvoicingTestingContractCreator,
)


@tagged("-at_install", "post_install")
class TestServiceInvoicingComponents(
    TransactionCase, ServiceInvoicingTestingContractCreator
):
    # TODO: Test configuration journal correctly defined
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_service_invoicing_wizard_creation_ok(self):
        company = self.env.ref("base.main_company")
        product_category_platform_pack = self.env.ref(
            "energy_communities_service_invoicing.product_category_platform_pack"
        ).with_company(company)
        self.assertEqual(
            product_category_platform_pack.service_invoicing_sale_journal_id.id, 11
        )
        # given a service invoicing contract created from wizard
        creation_wizard = self._get_service_invoicing_creation_wizard()
        contract_view = creation_wizard.execute_create()
        contract = self.env["contract.contract"].browse(int(contract_view["res_id"]))
        # the contract is defined based on wizard values
        self.assertTrue(contract.company_id, company)
        self.assertTrue(bool(contract))
        self.assertEqual(contract.status, "paused")
        self.assertEqual(contract.date_start, creation_wizard.execution_date)
        self.assertEqual(contract.partner_id, creation_wizard.company_id.partner_id)
        self.assertEqual(
            contract.community_company_id, creation_wizard.community_company_id
        )
        self.assertEqual(contract.pricelist_id, creation_wizard.pricelist_id)
        self.assertEqual(contract.payment_mode_id, creation_wizard.payment_mode_id)
        self.assertEqual(contract.discount, creation_wizard.discount)
        self.assertEqual(contract.recurring_next_date, creation_wizard.execution_date)
        self.assertEqual(contract.pack_type, PACK_TYPE_PLATFORM)
        self.assertEqual(contract.journal_id.id, 11)

    def test_service_invoicing_component_creation_metadata_ok(self):
        self._creation_workflow_meta_persistence_test(
            {
                "recurring_rule_mode": "fixed",
                "recurring_invoicing_fixed_type": "yearly",
                "fixed_invoicing_day": "07",
                "fixed_invoicing_month": "08",
            }
        )
        self._creation_workflow_meta_persistence_test(
            {
                "recurring_rule_type": "monthlylastday",
                "recurring_interval": 2,
                "recurring_invoicing_type": "pre-paid",
            }
        )

    def test_close_contract_ok(self):
        # given a service invoicing contract created from wizard
        contract = self._get_wizard_service_invoicing_contract()
        initial_recurring_next_date = contract.recurring_next_date
        self.assertEqual(contract.date_start, initial_recurring_next_date)
        contract_date = contract.date_start
        with contract_utils(self.env, contract) as component:
            component.close(contract_date)
        self.assertEqual(contract.status, "closed")
        self.assertEqual(contract.date_end, contract_date)
        self.assertEqual(contract.recurring_next_date, contract_date)

    def _creation_workflow_meta_persistence_test(self, cmetadata):
        # given a contract
        contract = self._get_component_service_invoicing_contract(cmetadata)
        # contract preserve sale order metadata values
        # on contract line
        contract_line = contract.contract_line_ids[0]
        for cfield in cmetadata:
            self.assertEqual(getattr(contract_line, cfield), cmetadata[cfield])
        for cfield in cmetadata:
            self.assertEqual(getattr(contract, cfield), cmetadata[cfield])
