from datetime import datetime

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


@tagged("-at_install", "post_install")
class TestServiceInvoicingRecurrencyModes(
    TransactionCase, ServiceInvoicingTestingContractCreator
):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_service_invoicing_recurrency_propagation(self):
        contract = self._get_component_service_invoicing_contract(
            recurring_rule_type="monthly",
            recurring_interval=1,
            recurring_invoicing_type="pre-paid",
        )
        self.assertEqual(contract.date_start, contract.contract_line_ids[0].date_start)
        self.assertEqual(
            contract.last_date_invoiced,
            contract.contract_line_ids[0].last_date_invoiced,
        )
        self.assertEqual(
            contract.recurring_next_date,
            contract.contract_line_ids[0].recurring_next_date,
        )
        self.assertEqual(
            contract.next_period_date_start,
            contract.contract_line_ids[0].next_period_date_start,
        )
        self.assertEqual(
            contract.next_period_date_end,
            contract.contract_line_ids[0].next_period_date_end,
        )
        contract.recurring_create_invoice()
        self.assertEqual(contract.date_start, contract.contract_line_ids[0].date_start)
        self.assertEqual(
            contract.last_date_invoiced,
            contract.contract_line_ids[0].last_date_invoiced,
        )
        self.assertEqual(
            contract.recurring_next_date,
            contract.contract_line_ids[0].recurring_next_date,
        )
        self.assertEqual(
            contract.next_period_date_start,
            contract.contract_line_ids[0].next_period_date_start,
        )
        self.assertEqual(
            contract.next_period_date_end,
            contract.contract_line_ids[0].next_period_date_end,
        )

    def test_service_invoicing_recurrency_dates(self):
        now = datetime.now().date()
        # REC-PRE-1
        contract = self._get_component_service_invoicing_contract(
            recurring_rule_type="monthly",
            recurring_interval=1,
            recurring_invoicing_type="pre-paid",
        )
        self.assertEqual(contract.date_start, now)
        self.assertEqual(contract.last_date_invoiced, False)
        self.assertEqual(contract.recurring_next_date, now)
        self.assertEqual(contract.next_period_date_start, now)
        self.assertEqual(
            contract.next_period_date_end,
            now + relativedelta(months=+1) + relativedelta(days=-1),
        )
        contract.recurring_create_invoice()
        self.assertEqual(
            contract.last_date_invoiced,
            now + relativedelta(months=+1) + relativedelta(days=-1),
        )
        self.assertEqual(contract.recurring_next_date, now + relativedelta(months=+1))
        self.assertEqual(
            contract.next_period_date_start, now + relativedelta(months=+1)
        )
        self.assertEqual(
            contract.next_period_date_end,
            contract.last_date_invoiced + relativedelta(months=+1),
        )
        # REC-PRE-2
        contract = self._get_component_service_invoicing_contract(
            recurring_rule_type="monthly",
            recurring_interval=2,
            recurring_invoicing_type="pre-paid",
        )
        self.assertEqual(contract.date_start, now)
        self.assertEqual(contract.last_date_invoiced, False)
        self.assertEqual(contract.recurring_next_date, now)
        self.assertEqual(contract.next_period_date_start, now)
        self.assertEqual(
            contract.next_period_date_end,
            now + relativedelta(months=+2) + relativedelta(days=-1),
        )
        contract.recurring_create_invoice()
        self.assertEqual(
            contract.last_date_invoiced,
            now + relativedelta(months=+2) + relativedelta(days=-1),
        )
        self.assertEqual(contract.recurring_next_date, now + relativedelta(months=+2))
        self.assertEqual(
            contract.next_period_date_start, now + relativedelta(months=+2)
        )
        self.assertEqual(
            contract.next_period_date_end,
            contract.last_date_invoiced + relativedelta(months=+2),
        )
        # REC-POST-2
        contract = self._get_component_service_invoicing_contract(
            recurring_rule_type="monthly",
            recurring_interval=2,
            recurring_invoicing_type="post-paid",
        )
        self.assertEqual(contract.date_start, now)
        self.assertEqual(contract.last_date_invoiced, False)
        self.assertEqual(contract.recurring_next_date, now + relativedelta(months=+2))
        self.assertEqual(contract.next_period_date_start, now)
        self.assertEqual(
            contract.next_period_date_end,
            now + relativedelta(months=+2) + relativedelta(days=-1),
        )
        contract.recurring_create_invoice()
        self.assertEqual(
            contract.last_date_invoiced,
            now + relativedelta(months=+2) + relativedelta(days=-1),
        )
        self.assertEqual(contract.recurring_next_date, now + relativedelta(months=+4))
        self.assertEqual(
            contract.next_period_date_start, now + relativedelta(months=+2)
        )
        self.assertEqual(
            contract.next_period_date_end,
            contract.last_date_invoiced + relativedelta(months=+2),
        )
