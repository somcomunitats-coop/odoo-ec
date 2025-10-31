from collections import namedtuple
from datetime import datetime

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities_service_invoicing.config import (
    PACK_TYPE_SELFCONSUMPTION,
)
from odoo.addons.energy_communities_service_invoicing.tests.service_invoicing_testing_contract_creator import (
    ServiceInvoicingTestingContractCreator,
)

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
class TestSelfconsumptionServiceInvoicing(
    TransactionCase, ServiceInvoicingTestingContractCreator
):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.selfconsumption = self.env.ref(
            "energy_selfconsumption.selfconsumption_1_community_1_demo"
        )
        self.inscription_1 = self.env.ref(
            "energy_selfconsumption.inscription_selfconsumption_1_selfconsumption_1_demo"
        )
        self.inscription_2 = self.env.ref(
            "energy_selfconsumption.inscription_selfconsumption_2_selfconsumption_1_demo"
        )
        self.subscription_5_inscription_5 = self.env.ref(
            "energy_communities_service_invoicing.subscription_5_community_1_demo"
        )
        self.subscription_5_supply_point_5 = self.env.ref(
            "energy_selfconsumption.supply_point_5_selfconsumption_1_demo"
        )
        self.selfconsumption_participation_1 = self.env[
            "energy_selfconsumptions.participation"
        ].search([("project_id", "=", self.selfconsumption.id), ("quantity", "=", 0.5)])

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

    def test_project_distribution_table_change_case_1(self):
        self._project_distribution_table_change_case(_TESTING_CASES["power_acquired"])

    def test_project_distribution_table_change_case_2(self):
        self._project_distribution_table_change_case(_TESTING_CASES["energy_delivered"])

    def test_project_distribution_table_change_case_3(self):
        self._project_distribution_table_change_case(_TESTING_CASES["energy_custom"])

    def _project_distribution_table_change_case(self, case):
        self._workflow_project_invoicing_mode_definition(case.invoicing_mode)
        self._workflow_project_contract_generation()
        self._workflow_change_inscriptions()
        contracts = self.selfconsumption.get_active_contracts()
        dict_contracts = {}
        for contract in contracts:
            dict_contracts[contract.id] = {
                "recurring_next_date": contract.recurring_next_date,
                "next_period_date_start": contract.next_period_date_start,
                "next_period_date_end": contract.next_period_date_end,
            }
        self._workflow_change_distribution_table()
        self._assert_project_contract_data()
        self.selfconsumption.set_new_distribution_table()
        self._assert_project_contracts_data_consistency_between_old_and_new(
            dict_contracts
        )

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
        contracts = self.selfconsumption.get_active_contracts()
        # ASSERT: only one generated contract
        self.assertEqual(len(contracts), 4)

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
                    "energy_communities_service_invoicing.community_1_payment_mode"
                ),
            }
        )
        contract_create_wizard.action_generate_contracts()
        return contract_create_wizard

    def _workflow_change_inscriptions(self):
        # New inscriptions
        mandate = self.env["account.banking.mandate"].search(
            [("partner_id", "in", [self.subscription_5_inscription_5.partner_id.id])]
        )
        self.inscription_5_new = self.env[
            "energy_selfconsumption.inscription_selfconsumption"
        ].create(
            {
                "project_id": self.selfconsumption.project_id.id,
                "effective_date": datetime.today(),
                "partner_id": self.subscription_5_inscription_5.partner_id.id,
                "company_id": self.selfconsumption.company_id.id,
                "mandate_id": mandate.id,
                "selfconsumption_project_id": self.selfconsumption.id,
                "annual_electricity_use": 1.00,
                "participation_id": self.selfconsumption_participation_1.id,
                "accept": True,
                "member": True,
                "supply_point_id": self.subscription_5_supply_point_5.id,
            }
        )
        self.inscription_5_new.write(
            {
                "participation_assigned_quantity": self.inscription_5_new.participation_quantity,
                "participation_real_quantity": self.inscription_5_new.participation_quantity,
            }
        )
        # Get inscriptions ids
        inscriptions_ids = [
            self.inscription_1.id,
            self.inscription_2.id,
            self.inscription_5_new.id,
        ]
        change_inscriptions_wizard = (
            self.env["energy_selfconsumption.change_state_inscription.wizard"]
            .with_context(active_ids=inscriptions_ids)
            .create({})
        )
        inscription_id_1 = change_inscriptions_wizard.change_state_inscription_lines_wizard_ids.filtered(
            lambda line: line.inscription_id.id == inscriptions_ids[0]
        )
        inscription_id_1.write({"participation_real_quantity": 0.25, "state": "change"})
        inscription_id_2 = change_inscriptions_wizard.change_state_inscription_lines_wizard_ids.filtered(
            lambda line: line.inscription_id.id == inscriptions_ids[1]
        )
        inscription_id_2.write({"participation_real_quantity": 0.00, "state": "change"})
        change_inscriptions_wizard.change_state_inscription()

    def _workflow_change_distribution_table(self):
        change_distribution_table_wizard = (
            self.env["change.distribution.table.import.wizard"]
            .with_context(default_selfconsumption_project_id=self.selfconsumption.id)
            .create({})
        )
        valid_lines = change_distribution_table_wizard.change_distribution_table_import_line_wizard_ids.filtered(
            lambda line: not (
                line.state == "change" and line.participation_real_quantity == 0
            )
        )
        create_distribution_table_wizard = (
            self.env["energy_selfconsumption.create_distribution_table.wizard"]
            .with_context(
                active_ids=valid_lines.inscription_id.ids,
                active_model="energy_selfconsumption.inscription_selfconsumption",
            )
            .create({})
        )
        create_distribution_table_wizard.write(
            {
                "distribute_excess": "yes",
            }
        )
        create_distribution_table_wizard.create_distribution_table()
        distribution_table = self.selfconsumption.distribution_table_ids.filtered(
            lambda table: table.state == "draft"
        )
        distribution_table.button_validate()

    def _assert_project_sale_orders_data(self, invoice_mode_wizard):
        sale_orders = self.selfconsumption.get_sale_orders()
        # ASSERT: sale order number
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

    def _assert_project_contract_data(self, contract_create_wizard=False):
        contracts = self.selfconsumption.get_active_contracts()
        # ASSERT: All contracts are active
        for contract in contracts:
            # ASSERT mandate correctly propagated
            inscription = contract.supply_point_assignation_id.get_inscription()
            self.assertTrue(bool(inscription.mandate_id))
            self.assertEqual(contract.mandate_id, inscription.mandate_id)
            # ASSERT contract is on the correct company_id
            self.assertEqual(contract.company_id, self.selfconsumption.company_id)
            # ASSERT contract journal definition ok
            self.assertEqual(
                contract.journal_id.id,
                self.env.ref(
                    "energy_selfconsumption.product_category_selfconsumption_pack"
                )
                .with_company(contract.company_id)
                .service_invoicing_sale_journal_id.id,
            )
            # ASSERT: sale order "confirmed"
            self.assertEqual(contract.sale_order_id.state, "sale")
            # ASSERT: contract has line recurrence
            self.assertEqual(contract.line_recurrence, True)
            # ASSERT: contract pack_type is selfconsumption
            self.assertEqual(contract.pack_type, PACK_TYPE_SELFCONSUMPTION)
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
                self.selfconsumption.contract_template_id.contract_line_ids[
                    0
                ].uom_id.id,
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
                contract.sale_order_id.commitment_date.strftime("%Y-%m-%d"),
            )
            self.assertEqual(
                contract.date_start.strftime("%Y-%m-%d"),
                contract.sale_order_id.commitment_date.strftime("%Y-%m-%d"),
            )
            # ASSERT: contract date_end not defined
            self.assertEqual(contract.contract_line_ids[0].date_end, False)
            self.assertEqual(contract.date_end, False)
            # ASSERT: contract pricelist_id same as sale_order
            self.assertEqual(
                contract.pricelist_id.id, contract.sale_order_id.pricelist_id.id
            )
            # ASSERT: contract pricelist_id same as project
            self.assertEqual(
                contract.pricelist_id.id, self.selfconsumption.pricelist_id.id
            )
            # ASSERT: contract payment_mode same as sale_order
            self.assertEqual(
                contract.payment_mode_id.id, contract.sale_order_id.payment_mode_id.id
            )
            # ASSERT: contract payment_mode correctly defined
            if contract_create_wizard:
                self.assertEqual(
                    contract.payment_mode_id.id, contract_create_wizard.payment_mode.id
                )

    def _assert_project_contracts_data_consistency_between_old_and_new(
        self, dict_contracts
    ):
        contracts = self.selfconsumption.get_active_contracts()
        for contract in contracts:
            if contract.predecessor_contract_id:
                self._assert_recurrency_config_consistency_between_old_and_new(
                    contract.predecessor_contract_id,
                    contract,
                    dict_contracts[contract.predecessor_contract_id.id][
                        "recurring_next_date"
                    ],
                    dict_contracts[contract.predecessor_contract_id.id][
                        "next_period_date_start"
                    ],
                    dict_contracts[contract.predecessor_contract_id.id][
                        "next_period_date_end"
                    ],
                )
