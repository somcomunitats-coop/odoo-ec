from collections import namedtuple
from datetime import date, datetime

from odoo.tests import common, tagged

from odoo.addons.energy_communities.config import PACK_TYPE_SHARE_RECURRING_FEE

SubscriptionPaymentTestingCase = namedtuple(
    "SubscriptionTestingCase",
    ["subscription_ref", "payment_date", "expected_recurring_next_date"],
)

_FIXED_RECURRENCY_DAY = 22
_FIXED_RECURRENCY_MONTH = 3

_TESTING_CASES = {
    "payment_before_fixed_day_recurrency": SubscriptionPaymentTestingCase(
        "energy_communities_cooperator.subscription_2_community_2_demo",
        date(
            datetime.now().year, _FIXED_RECURRENCY_MONTH - 1, _FIXED_RECURRENCY_DAY - 12
        ),
        date(datetime.now().year + 1, _FIXED_RECURRENCY_MONTH, _FIXED_RECURRENCY_DAY),
    ),
    "payment_equal_fixed_day_recurrency": SubscriptionPaymentTestingCase(
        "energy_communities_cooperator.subscription_1_community_2_demo",
        date(datetime.now().year, _FIXED_RECURRENCY_MONTH, _FIXED_RECURRENCY_DAY),
        date(datetime.now().year + 1, _FIXED_RECURRENCY_MONTH, _FIXED_RECURRENCY_DAY),
    ),
    "payment_after_fixed_day_recurrency": SubscriptionPaymentTestingCase(
        "energy_communities_cooperator.subscription_3_community_2_demo",
        date(
            datetime.now().year, _FIXED_RECURRENCY_MONTH + 4, _FIXED_RECURRENCY_DAY + 2
        ),
        date(datetime.now().year + 1, _FIXED_RECURRENCY_MONTH, _FIXED_RECURRENCY_DAY),
    ),
    "payment_after_fixed_day_recurrency_last_year": SubscriptionPaymentTestingCase(
        "energy_communities_cooperator.subscription_3_community_2_demo",
        date(
            datetime.now().year - 1,
            _FIXED_RECURRENCY_MONTH + 4,
            _FIXED_RECURRENCY_DAY + 2,
        ),
        date(datetime.now().year, _FIXED_RECURRENCY_MONTH, _FIXED_RECURRENCY_DAY),
    ),
    "payment_after_fixed_day_recurrency_next_year": SubscriptionPaymentTestingCase(
        "energy_communities_cooperator.subscription_3_community_2_demo",
        date(
            datetime.now().year + 1,
            _FIXED_RECURRENCY_MONTH + 4,
            _FIXED_RECURRENCY_DAY + 2,
        ),
        date(datetime.now().year + 2, _FIXED_RECURRENCY_MONTH, _FIXED_RECURRENCY_DAY),
    ),
}


@tagged("-at_install", "post_install")
class TestSubscriptionPaymentWithRecurringFee(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_subscription_payment_with_recurring_fee_case_1(self):
        self._subscription_payment_with_recurring_fee_case(
            _TESTING_CASES["payment_before_fixed_day_recurrency"]
        )

    def test_subscription_payment_with_recurring_fee_case_2(self):
        self._subscription_payment_with_recurring_fee_case(
            _TESTING_CASES["payment_equal_fixed_day_recurrency"]
        )

    def test_subscription_payment_with_recurring_fee_case_3(self):
        self._subscription_payment_with_recurring_fee_case(
            _TESTING_CASES["payment_after_fixed_day_recurrency"]
        )

    def test_subscription_payment_with_recurring_fee_case_4(self):
        self._subscription_payment_with_recurring_fee_case(
            _TESTING_CASES["payment_after_fixed_day_recurrency_last_year"]
        )

    def test_subscription_payment_with_recurring_fee_case_5(self):
        self._subscription_payment_with_recurring_fee_case(
            _TESTING_CASES["payment_after_fixed_day_recurrency_next_year"]
        )

    def _subscription_payment_with_recurring_fee_case(self, case):
        # GIVEN a draft subscription request
        subscription_request = self.env.ref(case.subscription_ref)
        # ASSERT: Previously to validation there is no sale order linked to the SR
        self.assertFalse(bool(subscription_request.service_invoicing_sale_order_id))
        # WORKFLOW: we validate the subscription request
        subscription_request.validate_subscription_request_with_company()
        # ASSERT: After validation a sale order has been linked to the SR
        self.assertTrue(bool(subscription_request.service_invoicing_sale_order_id))
        # GIVEN the partner related membership
        partner = subscription_request.partner_id
        membership = self.env["cooperative.membership"].search(
            [
                ("company_id", "=", subscription_request.company_id.id),
                ("partner_id", "=", partner.id),
            ]
        )
        # ASSERT: the membership exists
        self.assertTrue(bool(membership))
        # ASSERT: partner is still not effective cooperator
        self.assertFalse(membership.member)
        # ASSERT: partner has no related contracts
        self.assertFalse(bool(self._get_partner_contract(partner)))
        # WORKFLOW: we pay the subscription's related invoice
        self._pay_invoice(
            subscription_request.capital_release_request[0], case.payment_date
        )
        # ASSERT: related partner is now effective cooperator
        self.assertTrue(membership.member)
        # ASSERT: Now we have a recurrent fixed date contract related
        new_contract = self._get_partner_contract(partner)
        self.assertTrue(bool(new_contract))
        # ASSERT: New contract status is active
        self.assertEqual(new_contract.status, "in_progress")
        # ASSERT: New contract is linked to partner membership
        self.assertEqual(new_contract, membership.service_invoicing_id)
        # ASSERT: New contract has correct recurrency config
        self.assertEqual(new_contract.recurring_invoicing_type, "pre-paid")
        self.assertEqual(new_contract.recurring_rule_mode, "fixed")
        self.assertEqual(new_contract.recurring_invoicing_fixed_type, "yearly")
        self.assertEqual(int(new_contract.fixed_invoicing_day), _FIXED_RECURRENCY_DAY)
        self.assertEqual(
            int(new_contract.fixed_invoicing_month), _FIXED_RECURRENCY_MONTH
        )
        self.assertEqual(new_contract.date_start, case.expected_recurring_next_date)
        self.assertEqual(
            new_contract.recurring_next_date, case.expected_recurring_next_date
        )
        self.assertEqual(new_contract.pack_type, PACK_TYPE_SHARE_RECURRING_FEE)

    def _pay_invoice(self, invoice, payment_date):
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create(
            {
                "payment_date": payment_date,
            }
        )._create_payments()

    def _get_partner_contract(self, partner):
        return self.env["contract.contract"].search(
            [("partner_id", "=", partner.id)], limit=1
        )
