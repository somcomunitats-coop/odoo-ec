from dateutil.relativedelta import relativedelta

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)


@tagged("-at_install", "post_install")
class TestServiceInvoicingComponents(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_close_contract_ok(self):
        contract = self.env["contract.contract"].search([("id", "=", 67)])[0]
        initial_recurring_next_date = contract.recurring_next_date
        with contract_utils(self.env, contract) as component:
            component.set_contract_status_closed(contract.date_start)
        self.assertEqual(contract.recurring_next_date, initial_recurring_next_date)
