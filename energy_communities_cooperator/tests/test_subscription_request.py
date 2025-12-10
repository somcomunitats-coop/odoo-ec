from functools import partial

from odoo import _
from odoo.exceptions import ValidationError
from odoo.tests import common

from odoo.addons.account.models import AccountMove

from ..config import MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF


class TestSubscriptionRequest(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpRegistry()

    def setUp(self):
        super().setUp()
        self.maxDiff = None

        # Subscription request
        self.base_subscription = self.env.ref(
            "energy_communities_service_invoicingse.subscription_6_community_1_demo"
        )

    def _get_subscription_request(self, subscription_mode):
        product_categ = self.env.ref(
            MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF[subscription_mode]
        )
        product = self.env["product.template"].search(
            [
                ("categ_id", "=", product_categ.id),
                ("company_id", "=", self.base_subscription.company_id.id),
            ],
            limit=1,
        )
        subscription_request = self.base_susbscription.copy(
            {"share_product_id": product.id}
        )

        assert (
            subscription_request.share_product_categ_id.id == product_categ.id
        ), f"Product category from request {subscription_request.share_product_categ_id.name} must be {product_categ.name}"

        return subscription_request

    _get_member_subscription_request = partial(_get_subscription_request, "member")

    def test__validate_subscription_request__member_ok(self):
        # given a member subscription request
        member_subscription_request = self._get_member_subscription_request()

        # when we validate that subscription_request
        invoice = member_subscription_request.validate_subscription_request()

        self.assertIsInstance(invoice, AccountMove)
        # a correct invoice has been created

        # and a new partner has been linked to the subscription request

        # and a candidate membership is also linked to the partner

        # and subscription request is done

    def test__validate_subscription_request__member_already_exists(self):
        # given a member subscription request
        member_subscription_request = self._get_member_subscription_request()

        # if we validate that subscrition request
        member_subscription_request.validate_subscription_request()
        # and we create another subscription request for the same member
        duplicate_subscription = self._get_member_subscription_request()
        # when we validate this subscription, then a validationerror is raised

        with self.assertRaises(ValidationError) as excp_manager:
            duplicate_subscription.validate_subscription_request()

        self.assertEqual(
            str(excp_manager.exception),
            _("There is an existing account for this vat number on this community. "),
        )
