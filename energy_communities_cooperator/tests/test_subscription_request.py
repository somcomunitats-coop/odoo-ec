import unittest
from functools import partial

from odoo import _
from odoo.exceptions import ValidationError
from odoo.tests import Form, common

from odoo.addons.account.models.account_move import AccountMove

from ..config import MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF
from ..models.subscription_request import SubscriptionRequest
from .testing_cases import SUBSCRIPTION_REQUEST_PARAMS


class TestSubscriptionRequest(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.maxDiff = None

        # Subscription request
        # self.base_subscription = self.env.ref(
        #     "energy_communities_service_invoicing.subscription_6_community_1_demo"
        # )

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
        subscription_request = self.base_subscription.copy(
            {"share_product_id": product.product_variant_id.id}
        )

        assert (
            subscription_request.share_product_categ_id.id == product_categ.id
        ), f"Product category from request {subscription_request.share_product_categ_id.name} must be {product_categ.name}"

        return subscription_request

    _get_member_subscription_request = partial(_get_subscription_request, "member")

    @unittest.skip("wip test")
    def test__create_subscription_request__member_ok(self):
        # given the necessary data to create a subscruption request
        subscription_request_params = SUBSCRIPTION_REQUEST_PARAMS

        # when we create a new subscription request in the form view
        subscription_form = Form(self.env["subscription.request"])
        for attr, value in subscription_request_params.items():
            try:
                setattr(subscription_form, attr, value)
            except AssertionError:
                pass
        subscription_request = subscription_form.save()

        # Then a new subscription request is created
        self.assertIsInstance(subscription_request, SubscriptionRequest)

    def test__validate_subscription_request__member_ok(self):
        # given a member subscription request
        member_subscription_request = self._get_subscription_request("member")

        # when we validate that subscription_request
        invoice = member_subscription_request.validate_subscription_request()
        # TODO: review this, this should be a invoice object but is a None
        print(invoice)

        self.assertIsInstance(invoice, AccountMove)
        # a correct invoice has been created

        # and a new partner has been linked to the subscription request

        # and a candidate membership is also linked to the partner

        # and subscription request is done

    def test__validate_subscription_request__invited_ok(self):
        # given a invited subscription request
        invited_subscription_request = self._get_subscription_request("invited")

        # when we validate that subscription_request
        invoice = invited_subscription_request.validate_subscription_request()
        # TODO: review this, this should be a invoice object but is a None
        print(invoice)

        self.assertIsInstance(invoice, AccountMove)
        # a correct invoice has been created

        # and a new partner has been linked to the subscription request

        # and a candidate membership is also linked to the partner

        # and subscription request is done

    def test__validate_subscription_request__voluntary_ok(self):
        # given a voluntary subscription request
        voluntary_subscription_request = self._get_subscription_request("voluntary")

        # when we validate that subscription_request
        invoice = voluntary_subscription_request.validate_subscription_request()
        # TODO: review this, this should be a invoice object but is a None
        print(invoice)

        self.assertIsInstance(invoice, AccountMove)
        # a correct invoice has been created

        # and a new partner has been linked to the subscription request

        # and a candidate membership is also linked to the partner

        # and subscription request is done

    def test__validate_subscription_request__member_already_exists(self):
        # given a member subscription request
        member_subscription_request = self._get_subscription_request("member")

        # if we validate that subscrition request
        member_subscription_request.validate_subscription_request()
        # and we create another subscription request for the same member
        duplicate_subscription = self._get_subscription_request("member")
        # when we validate this subscription, then a validationerror is raised

        with self.assertRaises(ValidationError) as excp_manager:
            duplicate_subscription.validate_subscription_request()

        self.assertEqual(
            str(excp_manager.exception),
            _("There is an existing account for this vat number on this community. "),
        )

    def test__validate_subscription_request__voluntary_no_partner(self):
        # given a voluntary subscription request
        voluntary_subscription_request = self._get_subscription_request("voluntary")

        # when we validate that subscription_request
        with self.assertRaises(ValidationError) as excp_manager:
            voluntary_subscription_request.validate_subscription_request()

        self.assertEqual(
            str(excp_manager.exception),
            _("You can't create a voluntary subscription share for a new cooperator."),
        )
