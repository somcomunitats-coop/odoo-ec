from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)

from .service_invoicing_testing_contract_creator import (
    ServiceInvoicingTestingContractCreator,
)

_TESTING_CASES = {
    "interval_monthly_2_prepaid": {
        "recurring_rule_type": "monthly",
        "recurring_interval": 2,
        "recurring_invoicing_type": "pre-paid",
    },
    "interval_monthly_2_postpaid": {
        "recurring_rule_type": "monthly",
        "recurring_interval": 2,
        "recurring_invoicing_type": "post-paid",
    },
    "interval_monthlylastday_2_prepaid": {
        "recurring_rule_type": "monthlylastday",
        "recurring_interval": 2,
        "recurring_invoicing_type": "pre-paid",
    },
    "interval_monthlylastday_2_postpaid": {
        "recurring_rule_type": "monthlylastday",
        "recurring_interval": 2,
        "recurring_invoicing_type": "post-paid",
    },
    "fixed_yearly_prepaid": {
        "recurring_rule_mode": "fixed",
        "recurring_invoicing_fixed_type": "yearly",
        "fixed_invoicing_day": "07",
        "fixed_invoicing_month": "08",
        "recurring_invoicing_type": "pre-paid",
    },
    "fixed_yearly_postpaid": {
        "recurring_rule_mode": "fixed",
        "recurring_invoicing_fixed_type": "yearly",
        "fixed_invoicing_day": "07",
        "fixed_invoicing_month": "08",
        "recurring_invoicing_type": "post-paid",
    },
}

_EXECUTION_DATE = date(2025, 5, 12)


@tagged("-at_install", "post_install")
class TestServiceInvoicingRecurrency(
    TransactionCase, ServiceInvoicingTestingContractCreator
):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_service_invoicing_recurrency_dates_case_1(self):
        contract = self._get_component_service_invoicing_contract(
            _TESTING_CASES["interval_monthly_2_prepaid"], _EXECUTION_DATE
        )
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 5, 12),
            expected_last_date_invoiced=False,
            expected_recurring_next_date=date(2025, 5, 12),
            expected_next_period_date_start=date(2025, 5, 12),
            expected_next_period_date_end=date(2025, 7, 11),
        )
        contract.recurring_create_invoice()
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 5, 12),
            expected_last_date_invoiced=date(2025, 7, 11),
            expected_recurring_next_date=date(2025, 7, 12),
            expected_next_period_date_start=date(2025, 7, 12),
            expected_next_period_date_end=date(2025, 9, 11),
        )

    def test_service_invoicing_recurrency_dates_case_2(self):
        contract = self._get_component_service_invoicing_contract(
            _TESTING_CASES["interval_monthly_2_postpaid"], _EXECUTION_DATE
        )
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 5, 12),
            expected_last_date_invoiced=False,
            expected_recurring_next_date=date(2025, 7, 12),
            expected_next_period_date_start=date(2025, 5, 12),
            expected_next_period_date_end=date(2025, 7, 11),
        )
        contract.recurring_create_invoice()
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 5, 12),
            expected_last_date_invoiced=date(2025, 7, 11),
            expected_recurring_next_date=date(2025, 9, 12),
            expected_next_period_date_start=date(2025, 7, 12),
            expected_next_period_date_end=date(2025, 9, 11),
        )

    def test_service_invoicing_recurrency_dates_case_3(self):
        contract = self._get_component_service_invoicing_contract(
            _TESTING_CASES["interval_monthlylastday_2_prepaid"], _EXECUTION_DATE
        )
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 5, 12),
            expected_last_date_invoiced=False,
            expected_recurring_next_date=date(2025, 5, 12),
            expected_next_period_date_start=date(2025, 5, 12),
            expected_next_period_date_end=date(2025, 6, 30),
        )
        contract.recurring_create_invoice()
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 5, 12),
            expected_last_date_invoiced=date(2025, 6, 30),
            expected_recurring_next_date=date(2025, 7, 1),
            expected_next_period_date_start=date(2025, 7, 1),
            expected_next_period_date_end=date(2025, 8, 31),
        )

    def test_service_invoicing_recurrency_dates_case_4(self):
        contract = self._get_component_service_invoicing_contract(
            _TESTING_CASES["interval_monthlylastday_2_postpaid"], _EXECUTION_DATE
        )
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 5, 12),
            expected_last_date_invoiced=False,
            expected_recurring_next_date=date(2025, 6, 30),
            expected_next_period_date_start=date(2025, 5, 12),
            expected_next_period_date_end=date(2025, 6, 30),
        )
        contract.recurring_create_invoice()
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 5, 12),
            expected_last_date_invoiced=date(2025, 6, 30),
            expected_recurring_next_date=date(2025, 8, 31),
            expected_next_period_date_start=date(2025, 7, 1),
            expected_next_period_date_end=date(2025, 8, 31),
        )

    def test_service_invoicing_recurrency_dates_case_5(self):
        # CASE 5: fixed yearly prepaid (starts before invoicing day)
        contract = self._get_component_service_invoicing_contract(
            _TESTING_CASES["fixed_yearly_prepaid"], _EXECUTION_DATE
        )
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 5, 12),
            expected_last_date_invoiced=False,
            expected_recurring_next_date=date(2025, 8, 7),
            expected_next_period_date_start=date(2025, 8, 7),
            expected_next_period_date_end=date(2026, 8, 6),
        )
        contract.recurring_create_invoice()
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 5, 12),
            expected_last_date_invoiced=date(2026, 8, 6),
            expected_recurring_next_date=date(2026, 8, 7),
            expected_next_period_date_start=date(2026, 8, 7),
            expected_next_period_date_end=date(2027, 8, 6),
        )

    def test_service_invoicing_recurrency_dates_case_6(self):
        # CASE 6: fixed yearly prepaid (starts after invoicing day)
        contract = self._get_component_service_invoicing_contract(
            _TESTING_CASES["fixed_yearly_prepaid"], date(2025, 11, 20)
        )
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 11, 20),
            expected_last_date_invoiced=False,
            expected_recurring_next_date=date(2026, 8, 7),
            expected_next_period_date_start=date(2026, 8, 7),
            expected_next_period_date_end=date(2027, 8, 6),
        )
        contract.recurring_create_invoice()
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 11, 20),
            expected_last_date_invoiced=date(2027, 8, 6),
            expected_recurring_next_date=date(2027, 8, 7),
            expected_next_period_date_start=date(2027, 8, 7),
            expected_next_period_date_end=date(2028, 8, 6),
        )

    def test_service_invoicing_recurrency_dates_case_7(self):
        # CASE 7: fixed yearly postpaid (starts before invoicing day)
        contract = self._get_component_service_invoicing_contract(
            _TESTING_CASES["fixed_yearly_postpaid"], _EXECUTION_DATE
        )
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 5, 12),
            expected_last_date_invoiced=False,
            expected_recurring_next_date=date(2025, 8, 7),
            expected_next_period_date_start=date(2025, 5, 12),
            expected_next_period_date_end=date(2025, 8, 6),
        )
        contract.recurring_create_invoice()
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 5, 12),
            expected_last_date_invoiced=date(2025, 8, 6),
            expected_recurring_next_date=date(2026, 8, 7),
            expected_next_period_date_start=date(2025, 8, 7),
            expected_next_period_date_end=date(2026, 8, 6),
        )

    def test_service_invoicing_recurrency_dates_case_8(self):
        # CASE 8: fixed yearly postpaid (starts after invoicing day)
        contract = self._get_component_service_invoicing_contract(
            _TESTING_CASES["fixed_yearly_postpaid"], date(2025, 11, 20)
        )
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 11, 20),
            expected_last_date_invoiced=False,
            expected_recurring_next_date=date(2026, 8, 7),
            expected_next_period_date_start=date(2025, 11, 20),
            expected_next_period_date_end=date(2026, 8, 6),
        )
        contract.recurring_create_invoice()
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2025, 11, 20),
            expected_last_date_invoiced=date(2026, 8, 6),
            expected_recurring_next_date=date(2027, 8, 7),
            expected_next_period_date_start=date(2026, 8, 7),
            expected_next_period_date_end=date(2027, 8, 6),
        )

    def test_service_invoicing_recurrency_dates_case_9(self):
        # CASE 9: fixed yearly prepaid (starts same day as invoicing day)
        contract = self._get_component_service_invoicing_contract(
            _TESTING_CASES["fixed_yearly_prepaid"], date(2026, 8, 7)
        )
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2026, 8, 7),
            expected_last_date_invoiced=False,
            expected_recurring_next_date=date(2026, 8, 7),
            expected_next_period_date_start=date(2026, 8, 7),
            expected_next_period_date_end=date(2027, 8, 6),
        )
        contract.recurring_create_invoice()
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2026, 8, 7),
            expected_last_date_invoiced=date(2027, 8, 6),
            expected_recurring_next_date=date(2027, 8, 7),
            expected_next_period_date_start=date(2027, 8, 7),
            expected_next_period_date_end=date(2028, 8, 6),
        )

    def test_service_invoicing_recurrency_dates_case_10(self):
        # CASE 10: fixed yearly postpaid (starts same day as invoicing day)
        contract = self._get_component_service_invoicing_contract(
            _TESTING_CASES["fixed_yearly_postpaid"], date(2026, 8, 7)
        )
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2026, 8, 7),
            expected_last_date_invoiced=False,
            expected_recurring_next_date=date(2027, 8, 7),
            expected_next_period_date_start=date(2026, 8, 7),
            expected_next_period_date_end=date(2027, 8, 6),
        )
        contract.recurring_create_invoice()
        self._assert_recurrency_dates(
            contract,
            expected_date_start=date(2026, 8, 7),
            expected_last_date_invoiced=date(2027, 8, 6),
            expected_recurring_next_date=date(2028, 8, 7),
            expected_next_period_date_start=date(2027, 8, 7),
            expected_next_period_date_end=date(2028, 8, 6),
        )

    def test_service_invoicing_wizard_config_recurrency_propagation_case_1(self):
        self._service_invoicing_reopen_recurrency_case(
            _TESTING_CASES["interval_monthly_2_prepaid"]
        )

    def test_service_invoicing_wizard_config_recurrency_propagation_case_2(self):
        self._service_invoicing_reopen_recurrency_case(
            _TESTING_CASES["interval_monthly_2_postpaid"]
        )

    def test_service_invoicing_wizard_config_recurrency_propagation_case_3(self):
        self._service_invoicing_reopen_recurrency_case(
            _TESTING_CASES["interval_monthlylastday_2_prepaid"]
        )

    def test_service_invoicing_wizard_config_recurrency_propagation_case_4(self):
        self._service_invoicing_reopen_recurrency_case(
            _TESTING_CASES["interval_monthlylastday_2_postpaid"]
        )

    def test_service_invoicing_wizard_config_recurrency_propagation_case_5(self):
        self._service_invoicing_reopen_recurrency_case(
            _TESTING_CASES["fixed_yearly_prepaid"]
        )

    def test_service_invoicing_wizard_config_recurrency_propagation_case_6(self):
        self._service_invoicing_reopen_recurrency_case(
            _TESTING_CASES["fixed_yearly_postpaid"]
        )

    def service_invoicing_wizard_config_recurrency_propagation_case(self, case):
        # given a service invoicing contract created from wizard
        demo_contract_template_line = self.env.ref(
            "energy_communities_service_invoicing.demo_platform_pack_contract_template"
        ).contract_line_ids[0]
        demo_contract_template_line.write(case)
        creation_wizard = self._get_service_invoicing_creation_wizard()
        contract_view = creation_wizard.execute_create()
        contract = self.env["contract.contract"].browse(int(contract_view["res_id"]))
        self._assert_recurrency_config_consistency(
            contract.contract_line_ids[0], demo_contract_template_line
        )
        self._assert_recurrency_config_consistency(
            contract, demo_contract_template_line
        )
        self._assert_recurrency_config_consistency(
            contract, contract.contract_line_ids[0]
        )
        self._assert_recurrency_dates_consistency(
            contract, contract.contract_line_ids[0]
        )
        contract.unlink()

    def test_service_invoicing_component_meta_recurrency_propagation_case_1(self):
        self.service_invoicing_component_meta_recurrency_propagation_case(
            _TESTING_CASES["interval_monthly_2_prepaid"]
        )

    def test_service_invoicing_component_meta_recurrency_propagation_case_2(self):
        self.service_invoicing_component_meta_recurrency_propagation_case(
            _TESTING_CASES["interval_monthly_2_postpaid"]
        )

    def test_service_invoicing_component_meta_recurrency_propagation_case_3(self):
        self.service_invoicing_component_meta_recurrency_propagation_case(
            _TESTING_CASES["interval_monthlylastday_2_prepaid"]
        )

    def test_service_invoicing_component_meta_recurrency_propagation_case_4(self):
        self.service_invoicing_component_meta_recurrency_propagation_case(
            _TESTING_CASES["interval_monthlylastday_2_postpaid"]
        )

    def test_service_invoicing_component_meta_recurrency_propagation_case_5(self):
        self.service_invoicing_component_meta_recurrency_propagation_case(
            _TESTING_CASES["fixed_yearly_prepaid"]
        )

    def test_service_invoicing_component_meta_recurrency_propagation_case_6(self):
        self.service_invoicing_component_meta_recurrency_propagation_case(
            _TESTING_CASES["fixed_yearly_postpaid"]
        )

    def service_invoicing_component_meta_recurrency_propagation_case(self, case):
        # given a contract
        contract = self._get_component_service_invoicing_contract(case, _EXECUTION_DATE)
        # it's correctly configured between contract and contract_lines
        self._assert_recurrency_config_consistency(
            contract, contract.contract_line_ids[0]
        )
        self._assert_recurrency_dates_consistency(
            contract, contract.contract_line_ids[0]
        )
        # if we generate an invoice
        contract.recurring_create_invoice()
        # configuration still ok
        self._assert_recurrency_config_consistency(
            contract, contract.contract_line_ids[0]
        )
        self._assert_recurrency_dates_consistency(
            contract, contract.contract_line_ids[0]
        )

    def test_service_invoicing_reopen_recurrency_case_1(self):
        self._service_invoicing_reopen_recurrency_case(
            _TESTING_CASES["interval_monthly_2_prepaid"]
        )

    def test_service_invoicing_reopen_recurrency_case_2(self):
        self._service_invoicing_reopen_recurrency_case(
            _TESTING_CASES["interval_monthly_2_postpaid"]
        )

    def test_service_invoicing_reopen_recurrency_case_3(self):
        self._service_invoicing_reopen_recurrency_case(
            _TESTING_CASES["interval_monthlylastday_2_prepaid"]
        )

    def test_service_invoicing_reopen_recurrency_case_4(self):
        self._service_invoicing_reopen_recurrency_case(
            _TESTING_CASES["interval_monthlylastday_2_postpaid"]
        )

    def test_service_invoicing_reopen_recurrency_case_5(self):
        self._service_invoicing_reopen_recurrency_case(
            _TESTING_CASES["fixed_yearly_prepaid"]
        )

    def test_service_invoicing_reopen_recurrency_case_6(self):
        self._service_invoicing_reopen_recurrency_case(
            _TESTING_CASES["fixed_yearly_postpaid"]
        )

    def _service_invoicing_reopen_recurrency_case(self, case):
        # given a contract
        contract = self._get_component_service_invoicing_contract(case, _EXECUTION_DATE)
        with contract_utils(self.env, contract) as component:
            record = component.work.record
            record.recurring_create_invoice()
            initial_recurring_next_date = record.recurring_next_date
            initial_next_period_date_start = record.next_period_date_start
            initial_next_period_date_end = record.next_period_date_end
            initial_last_date_invoiced = record.last_date_invoiced
            # we close it and then reopen
            component.close(initial_last_date_invoiced)
            reopen_date = initial_last_date_invoiced + relativedelta(days=+1)
            new_contract = component.reopen(
                reopen_date,
                record.pricelist_id,
                record.pack_id,
            )
            new_contract_line = new_contract.contract_line_ids[0]
            # new recurrency values match previous ones
            self._assert_recurrency_config_consistency_between_old_and_new(
                record,
                new_contract,
                initial_recurring_next_date,
                initial_next_period_date_start,
                initial_next_period_date_end,
            )

    def test_service_invoicing_modification_recurrency_case_1(self):
        self._service_invoicing_modification_recurrency_case(
            _TESTING_CASES["interval_monthly_2_prepaid"]
        )

    def test_service_invoicing_modification_recurrency_case_2(self):
        self._service_invoicing_modification_recurrency_case(
            _TESTING_CASES["interval_monthly_2_postpaid"]
        )

    def test_service_invoicing_modification_recurrency_case_3(self):
        self._service_invoicing_modification_recurrency_case(
            _TESTING_CASES["interval_monthlylastday_2_prepaid"]
        )

    def test_service_invoicing_modification_recurrency_case_4(self):
        self._service_invoicing_modification_recurrency_case(
            _TESTING_CASES["interval_monthlylastday_2_postpaid"]
        )

    def test_service_invoicing_modification_recurrency_case_5(self):
        self._service_invoicing_modification_recurrency_case(
            _TESTING_CASES["fixed_yearly_prepaid"]
        )

    def test_service_invoicing_modification_recurrency_case_6(self):
        self._service_invoicing_modification_recurrency_case(
            _TESTING_CASES["fixed_yearly_postpaid"]
        )

    def _service_invoicing_modification_recurrency_case(self, case):
        # given a contract
        contract = self._get_component_service_invoicing_contract(case, _EXECUTION_DATE)
        # we modify it
        with contract_utils(self.env, contract) as component:
            record = component.work.record
            record.recurring_create_invoice()
            initial_recurring_next_date = record.recurring_next_date
            initial_next_period_date_start = record.next_period_date_start
            initial_next_period_date_end = record.next_period_date_end
            initial_last_date_invoiced = record.last_date_invoiced
            modification_date = initial_last_date_invoiced + relativedelta(days=+1)
            new_contract = component.modify(
                modification_date,
                "modify_discount",
                pricelist_id=None,
                pack_id=None,
                discount=12,
                payment_mode_id=None,
            )
            # new recurrency values match previous ones
            self._assert_recurrency_config_consistency_between_old_and_new(
                record,
                new_contract,
                initial_recurring_next_date,
                initial_next_period_date_start,
                initial_next_period_date_end,
            )

    # TODO: test_service_invoicing_closing_recurrency(self):

    def _assert_recurrency_dates(
        self,
        contract,
        expected_date_start,
        expected_last_date_invoiced,
        expected_recurring_next_date,
        expected_next_period_date_start,
        expected_next_period_date_end,
    ):
        self.assertEqual(contract.date_start, expected_date_start)
        self.assertEqual(contract.last_date_invoiced, expected_last_date_invoiced)
        self.assertEqual(contract.recurring_next_date, expected_recurring_next_date)
        self.assertEqual(
            contract.next_period_date_start, expected_next_period_date_start
        )
        self.assertEqual(contract.next_period_date_end, expected_next_period_date_end)

    def _assert_recurrency_config_consistency(self, obj_1, obj_2):
        self.assertEqual(obj_1.recurring_rule_type, obj_2.recurring_rule_type)
        self.assertEqual(obj_1.recurring_interval, obj_2.recurring_interval)
        self.assertEqual(obj_1.recurring_invoicing_type, obj_2.recurring_invoicing_type)
        self.assertEqual(obj_1.recurring_rule_mode, obj_2.recurring_rule_mode)
        self.assertEqual(
            obj_1.recurring_invoicing_fixed_type, obj_2.recurring_invoicing_fixed_type
        )
        self.assertEqual(obj_1.fixed_invoicing_day, obj_2.fixed_invoicing_day)
        self.assertEqual(obj_1.fixed_invoicing_month, obj_2.fixed_invoicing_month)

    def _assert_recurrency_dates_consistency(self, obj_1, obj_2):
        self.assertEqual(obj_1.date_start, obj_2.date_start)
        self.assertEqual(obj_1.last_date_invoiced, obj_2.last_date_invoiced)
        self.assertEqual(obj_1.next_period_date_start, obj_2.next_period_date_start)
        self.assertEqual(obj_1.next_period_date_end, obj_2.next_period_date_end)
        self.assertEqual(obj_1.recurring_next_date, obj_2.recurring_next_date)
