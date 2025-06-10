from collections import namedtuple

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

SelfconsumptionTestingCase = namedtuple(
    "SelfconsumptionTestingCase", ["pack_product_ref", "invoicing_mode"]
)

_TESTING_CASES = {
    "power_acquired": SelfconsumptionTestingCase(
        "energy_selfconsumption.product_product_power_acquired_product_pack_template",
        "power_acquired",
    ),
    "energy_delivered": SelfconsumptionTestingCase(
        "energy_selfconsumption.product_product_energy_delivered_product_pack_template",
        "energy_delivered",
    ),
    "energy_custom": SelfconsumptionTestingCase(
        "energy_selfconsumption.product_product_energy_custom_product_pack_template",
        "energy_custom",
    ),
}


@tagged("-at_install", "post_install", "energy_selfconsumption")
class TestSelfconsumptionServiceInvoicing(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.selfconsumption = self.env.ref(
            "energy_selfconsumption.selfconsumption_1_community_1_demo"
        )

    def test_project_invoicing_mode_definition_case_1(self):
        self._project_invoicing_mode_definition_case(_TESTING_CASES["power_acquired"])

    def test_project_invoicing_mode_definition_case_2(self):
        self._project_invoicing_mode_definition_case(_TESTING_CASES["energy_delivered"])

    def test_project_invoicing_mode_definition_case_3(self):
        self._project_invoicing_mode_definition_case(_TESTING_CASES["energy_custom"])

    def test_project_contract_generation_case_1(self):
        self._project_contract_generation_case(_TESTING_CASES["power_acquired"])

    def test_project_contract_generation_case_2(self):
        self._project_contract_generation_case(_TESTING_CASES["energy_delivered"])

    def test_project_contract_generation_case_3(self):
        self._project_contract_generation_case(_TESTING_CASES["energy_custom"])

    # TODO: test_project_distribution_table_change_case_xy()
    # def test_project_distribution_table_change_case_1(self):
    #     self._project_distribution_table_change_case(_TESTING_CASES["power_acquired"])
    # def _project_distribution_table_change_case(self, case):
    #     self._workflow_project_invoicing_mode_definition(case.invoicing_mode)
    #     self._workflow_project_contract_generation()
    #     self._workflow_change_inscriptions()
    #     self._workflow_change_distribution_table()
    #     self._assert_project_contract_data() # Reuse assertions from first creation but on new contracts
    #     self._assert_project_contracts_data_consistency_between_old_and_new() # Check recurrence dates match between new and old

    def _project_invoicing_mode_definition_case(self, case):
        # WORKFLOW: invoicing mode execution
        invoice_mode_wizard = self._workflow_project_invoicing_mode_definition(
            case.invoicing_mode
        )
        # ASSERTIONS
        self._assert_project_sale_orders_data(invoice_mode_wizard)
        self._assert_project_invoicing_mode_data(
            invoice_mode_wizard, self.env.ref(case.pack_product_ref)
        )
        # TODO: Assert Dates Match properly with expected??

    def _project_contract_generation_case(self, case):
        # WORKFLOW: invoicing mode execution and contract generation
        self._workflow_project_invoicing_mode_definition(case.invoicing_mode)
        contract_create_wizard = self._workflow_project_contract_generation()
        # ASSERTIONS
        self._assert_project_contract_data(contract_create_wizard)
        # TODO: Assert Dates Match properly with expected

    def _workflow_project_invoicing_mode_definition(self, invoicing_mode):
        invoice_mode_wizard = self.env[
            "energy_selfconsumption.define_invoicing_mode.wizard"
        ].create(
            {
                "selfconsumption_id": self.selfconsumption.id,
                "invoicing_mode": invoicing_mode,
                "price": 11,
                "recurring_rule_type": "quarterly",
                "recurring_interval": 2,
                "recurring_invoicing_type": "post-paid",
            }
        )
        invoice_mode_wizard.create_contract_template()
        return invoice_mode_wizard

    def _workflow_project_contract_generation(self):
        contract_create_wizard = self.env[
            "energy_selfconsumption.contract_generation.wizard"
        ].create(
            {
                "selfconsumption_id": self.selfconsumption.id,
                "payment_mode": self.ref(
                    "account_banking_sepa_direct_debit.payment_mode_inbound_sepa_dd1"
                ),
            }
        )
        contract_create_wizard.action_generate_contracts()
        return contract_create_wizard

    def _assert_project_sale_orders_data(self, invoice_mode_wizard):
        sale_orders = self.selfconsumption.get_sale_orders()
        # ASSERT: sale order number
        self.assertEqual(len(sale_orders), 5)
        # ASSERT: Sale order has metadata for recurring_rule_type
        meta_recurring_rule_type = sale_orders.metadata_line_ids.filtered(
            lambda metadata: metadata.key == "recurring_rule_type"
            and metadata.order_id == sale_orders[0]
        )
        self.assertEqual(True, bool(meta_recurring_rule_type))
        self.assertEqual(
            invoice_mode_wizard.recurring_rule_type, meta_recurring_rule_type.value
        )
        # ASSERT: Sale order has metadata for recurring_interval
        meta_recurring_interval = sale_orders.metadata_line_ids.filtered(
            lambda metadata: metadata.key == "recurring_interval"
            and metadata.order_id == sale_orders[0]
        )
        self.assertEqual(True, bool(meta_recurring_interval))
        self.assertEqual(
            str(invoice_mode_wizard.recurring_interval), meta_recurring_interval.value
        )
        # ASSERT: Sale order has metadata for recurring_invoicing_type
        meta_recurring_invoicing_type = sale_orders.metadata_line_ids.filtered(
            lambda metadata: metadata.key == "recurring_invoicing_type"
            and metadata.order_id == sale_orders[0]
        )
        self.assertEqual(True, bool(meta_recurring_invoicing_type))
        self.assertEqual(
            invoice_mode_wizard.recurring_invoicing_type,
            meta_recurring_invoicing_type.value,
        )
        # ASSERT: Sale order has no date_end
        self.assertEqual(
            sale_orders[0].order_line[0].date_start,
            sale_orders[0].order_line[0].date_end,
        )

    def _assert_project_invoicing_mode_data(self, invoice_mode_wizard, pack_product):
        sale_orders = self.selfconsumption.get_sale_orders()
        # ASSERT: project product defined correctly
        self.assertEqual(
            self.selfconsumption.product_id.id, pack_product.product_variant_id.id
        )
        # ASSERT: project has same product as sale order
        self.assertEqual(
            self.selfconsumption.product_id.id,
            sale_orders[0].order_line[0].product_id.id,
        )
        # ASSERT: project has same contract template as sale order
        self.assertEqual(
            self.selfconsumption.contract_template_id.id,
            sale_orders[0].order_line[0].product_id.property_contract_template_id.id,
        )
        # ASSERT: project invoicing mode correctly defined
        self.assertEqual(
            invoice_mode_wizard.invoicing_mode, self.selfconsumption.invoicing_mode
        )
        # ASSERT: project has recurring_rule_type correctly defined
        self.assertEqual(
            invoice_mode_wizard.recurring_rule_type,
            self.selfconsumption.recurring_rule_type,
        )
        # ASSERT: project has recurring_interval correctly defined
        self.assertEqual(
            invoice_mode_wizard.recurring_interval,
            self.selfconsumption.recurring_interval,
        )
        # ASSERT: project has recurring_invoicing_type correctly defined
        self.assertEqual(
            invoice_mode_wizard.recurring_invoicing_type,
            self.selfconsumption.recurring_invoicing_type,
        )
        # ASSERT: project has pricelist_id correctly defined
        self.assertEqual(
            sale_orders[0].pricelist_id.id, self.selfconsumption.pricelist_id.id
        )
        # ASSERT: pricelist_id properly defined
        self.assertEqual(1, len(self.selfconsumption.pricelist_id.item_ids))
        self.assertEqual(
            pack_product.property_contract_template_id.contract_line_ids[
                0
            ].product_id.id,
            self.selfconsumption.pricelist_id.item_ids[0].product_id.id,
        )
        self.assertEqual(
            invoice_mode_wizard.price,
            self.selfconsumption.pricelist_id.item_ids[0].fixed_price,
        )

    def _assert_project_contract_data(self, contract_create_wizard):
        sale_orders = self.selfconsumption.get_sale_orders()
        contracts = self.selfconsumption.get_contracts()
        contract = contracts[0]
        # ASSERT: only one generated contract
        self.assertEqual(len(contracts), 5)
        # ASSERT: sale order "confirmed"
        self.assertEqual(sale_orders[0].state, "sale")
        # ASSERT: contract has line recurrence
        self.assertEqual(contract.line_recurrence, True)
        # ASSERT: contract pack_type is selfconsumption
        self.assertEqual(contract.pack_type, "selfconsumption_pack")
        # ASSERT: contract contract_template same as project contract_template
        self.assertEqual(
            contract.contract_template_id.id,
            self.selfconsumption.contract_template_id.id,
        )
        # ASSERT: contract product uses pricelist
        self.assertEqual(contract.contract_line_ids[0].automatic_price, True)
        # ASSERT: contract product same as project product
        self.assertEqual(
            contract.contract_line_ids[0].product_id.id,
            self.selfconsumption.contract_template_id.contract_line_ids[
                0
            ].product_id.id,
        )
        # ASSERT: contract qty_type same as project
        self.assertEqual(
            contract.contract_line_ids[0].qty_type,
            self.selfconsumption.contract_template_id.contract_line_ids[0].qty_type,
        )
        # ASSERT: contract qty_formula_id in same as project
        self.assertEqual(
            contract.contract_line_ids[0].qty_formula_id.id,
            self.selfconsumption.contract_template_id.contract_line_ids[
                0
            ].qty_formula_id.id,
        )
        # ASSERT: contract uom_id same as project
        self.assertEqual(
            contract.contract_line_ids[0].uom_id.id,
            self.selfconsumption.contract_template_id.contract_line_ids[0].uom_id.id,
        )
        # ASSERT: contract recurring_rule_type same as project
        self.assertEqual(
            contract.contract_line_ids[0].recurring_rule_type,
            self.selfconsumption.recurring_rule_type,
        )
        # ASSERT: contract recurring_interval same as project
        self.assertEqual(
            contract.contract_line_ids[0].recurring_interval,
            self.selfconsumption.recurring_interval,
        )
        # ASSERT: contract recurring_invoicing_type same as project
        self.assertEqual(
            contract.contract_line_ids[0].recurring_invoicing_type,
            self.selfconsumption.recurring_invoicing_type,
        )
        # ASSERT: contract date_start same as sale order
        self.assertEqual(
            contract.contract_line_ids[0].date_start.strftime("%Y-%m-%d"),
            sale_orders[0].commitment_date.strftime("%Y-%m-%d"),
        )
        self.assertEqual(
            contract.date_start.strftime("%Y-%m-%d"),
            sale_orders[0].commitment_date.strftime("%Y-%m-%d"),
        )
        # ASSERT: contract date_end not defined
        self.assertEqual(contract.contract_line_ids[0].date_end, False)
        self.assertEqual(contract.date_end, False)
        # ASSERT: contract pricelist_id same as sale_order
        self.assertEqual(contract.pricelist_id.id, sale_orders[0].pricelist_id.id)
        # ASSERT: contract pricelist_id same as project
        self.assertEqual(contract.pricelist_id.id, self.selfconsumption.pricelist_id.id)
        # ASSERT: contract payment_mode same as sale_order
        self.assertEqual(contract.payment_mode_id.id, sale_orders[0].payment_mode_id.id)
        # ASSERT: contract payment_mode correctly defined
        self.assertEqual(
            contract.payment_mode_id.id, contract_create_wizard.payment_mode.id
        )
