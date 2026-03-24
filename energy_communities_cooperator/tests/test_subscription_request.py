import unittest
from datetime import date
from functools import partial

from odoo import _
from odoo.exceptions import ValidationError
from odoo.tests import Form, common
from odoo.tests.common import tagged

from odoo.addons.account.models.account_move import AccountMove

from ..config import MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF
from ..models.subscription_request import SubscriptionRequest
from ..schemas import MemberShipMode
from .testing_cases import SUBSCRIPTION_REQUEST_PARAMS


@tagged("-at_install", "post_install")
class TestSubscriptionRequest(common.TransactionCase):
    def setUpComponents(self):
        builder = self.env["component.builder"]
        # build the components of every installed addons
        comp_registry = builder._init_global_registry()
        # ensure that we load only the components of the 'installed'
        # modules, not 'to install', which means we load only the
        # dependencies of the tested addons, not the siblings or
        # children addons
        builder.build_registry(comp_registry, states=("installed",))
        # build the componenets fot energy_communities_invoicing
        builder.load_components("energy_communities_cooperator", comp_registry)
        self.env.context = dict(self.env.context, components_registry=comp_registry)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.setUpComponents()
        self.maxDiff = None

        # Subscription request
        self.base_subscription = self.env.ref(
            "energy_communities_service_invoicing.subscription_6_community_1_demo"
        )
        # Journal
        self.journal = self.env["account.journal"].search(
            [
                ("type", "=", "bank"),
                ("company_id", "=", self.base_subscription.company_id.id),
            ]
        )[0]

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
            {"ordered_parts": 5, "share_product_id": product.product_variant_id.id}
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

        self.assertIsInstance(invoice, AccountMove)
        # a correct invoice has been created

        # and a new partner has been linked to the subscription request

        # and a candidate membership is also linked to the partner

        # and subscription request is done

    def test__validate_subscription_request__invited_ok(self):
        # given a invited subscription request
        invited_subscription_request = self._get_subscription_request("invited")
        invited_subscription_request.share_product_id.taxes_id = None

        # when we validate that subscription_request
        invoice = invited_subscription_request.validate_subscription_request()
        # TODO: review this, this should be a invoice object but is a None

        self.assertIsInstance(invoice, AccountMove)
        # a correct invoice has been created

        # and a new partner has been linked to the subscription request

        # and a candidate membership is also linked to the partner

        # and subscription request is done

    def test__subscription_request__invited2member(self):
        def get_invited_membership():
            invited_subscription_request = self._get_subscription_request("invited")
            invited_subscription_request.share_product_id.taxes_id = None
            invited_subscription_request.share_product_id.lst_price = 0
            invited_subscription_request.validate_subscription_request()
            return invited_subscription_request.partner_id.get_cooperative_membership(
                invited_subscription_request.company_id
            )

        def get_member_subscription_request(vat):
            return self._get_subscription_request("member")

        def pay_invoice(invoice):
            payment_form = Form(
                self.env["account.payment.register"].with_context(
                    active_ids=[invoice.id], active_model="account.move"
                )
            )
            payment_form.journal_id = self.journal
            payment_form.payment_date = date.today()
            payment_form.save().action_create_payments()

        # given a invited membership
        invited_membership = get_invited_membership()

        # and a member subscription request (for that invited partner = VAT)
        subscription_request = get_member_subscription_request(
            invited_membership.partner_id.vat
        )

        # when we validate that subscription request
        invoice = subscription_request.validate_subscription_request()
        # then the member subs.req. has same partner_id ofpre-existing invited membership
        self.assertEqual(subscription_request.partner_id, invited_membership.partner_id)

        # and the same memebership
        self.assertEqual(
            subscription_request.partner_id.get_cooperative_membership(
                subscription_request.company_id
            ).id,
            invited_membership.id,
        )

        # and the invited membership has been updated with the correct values
        self.assertEqual(
            invited_membership.membership_type, MemberShipMode.invited.value
        )
        self.assertTrue(invited_membership.effective_invited)
        self.assertEqual(invited_membership.cooperator_register_number, 0)
        self.assertTrue(invited_membership.coop_candidate)

        # when we pay the invoice
        pay_invoice(invoice)
        # invoice is paid
        self.assertEqual(invoice.payment_state, "paid")
        # and invited membership is now a member membership
        self.assertFalse(invited_membership.coop_candidate)
        self.assertEqual(
            invited_membership.membership_type, MemberShipMode.cooperator.value
        )
        self.assertTrue(invited_membership.member)
        self.assertNotEqual(invited_membership.cooperator_register_number, 0)
        self.assertFalse(invited_membership.effective_invited)
        self.assertEqual(
            invited_membership.cooperator_type,
            subscription_request.share_product_id.code,
        )

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
