from datetime import datetime

from faker import Faker

from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestSubscriptionPaymentWithRecurringFee(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_subscription_payment_with_recurring_fee(self):
        # given a validated subscription request
        subscription_request = self.env.ref(
            "energy_communities_cooperator.subscription_3_community_2_demo"
        )
        # with a partner
        partner = subscription_request.partner_id
        # and the partner related membership
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
        # if we pay the subscription's related invoice
        self._pay_invoice(subscription_request.capital_release_request[0])
        # ASSERT: related partner is now effective cooperator
        self.assertTrue(membership.member)
        # ASSERT: Now we have a recurrent fixed date contract related
        new_contract = self._get_partner_contract(partner)
        self.assertTrue(bool(new_contract))

    def _pay_invoice(self, invoice):
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create(
            {
                "payment_date": datetime.now(),
            }
        )._create_payments()

    def _get_partner_contract(self, partner):
        return self.env["contract.contract"].search(
            [("partner_id", "=", partner.id)], limit=1
        )
