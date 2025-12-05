from functools import partial
from unittest.mock import patch

import requests

from odoo.http import Request
from odoo.tests.common import HttpCase, tagged

from odoo.addons.base_rest.tests.common import RegistryMixin

from ..config import (
    STATUS_CODE_CONSISTENCY_ERROR,
    STATUS_CODE_NOT_FOUND_ERROR,
    STATUS_CODE_UNAVAILABLE_ERROR,
)
from .testing_cases import (
    SUBSCRIPTION_FORM_SUBMISSION,
    SUBSCRIPTION_FORM_SUBMISSION_COMPANY_MEMBER,
)

COMMUNITY_1_EXT_ID = "ac3478d69a3c81fa62e60f5c3696165a4e5e6ac4"
COMMUNITY_2_EXT_ID = "c1dfd96eea8cc2b62785275bca38ac261256e278"
COMMUNITY_1_SHARE_1_EXT_ID = "7719a1c782a1ba91c031a682a0a2f8658209adbf"
COMMUNITY_1_SHARE_1_XML_ID = "cooperator.product_template_share_type_1_demo"
COMMUNITY_1_SHARE_2_EXT_ID = "fc074d501302eb2b93e2554793fcaf50b3bf7291"
COMMUNITY_1_SHARE_2_XML_ID = (
    "energy_communities_service_invoicing.product_template_share_type_3_demo"
)


@tagged("-at_install", "post_install")
class TestShareSubscriptionController(HttpCase, RegistryMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpRegistry()

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.timeout = 600
        self.client = partial(
            self.url_open,
            timeout=self.timeout,
        )

    def test_website_form_render__wrong_subscription_mode(self):
        # given http_client
        # when we call for the global subscription form page
        # with wrong subscription_mode
        response = self.client("/subscription/aaaa/{}".format(COMMUNITY_1_EXT_ID))
        # it throws a NotFound error
        self.assertEqual(response.status_code, STATUS_CODE_NOT_FOUND_ERROR)

    def test_website_form_render__wrong_company(self):
        # given http_client
        # when we call for the global subscription form page
        # with wrong company_ext_id
        response = self.client("/subscription/member/1234")
        # it throws a NotFound error
        self.assertEqual(response.status_code, STATUS_CODE_NOT_FOUND_ERROR)

    def test_website_form_render__wrong_subscription_mode_and_company(self):
        # given http_client
        # when we call for the global subscription form page
        # with wrong subscription_mode and company_ext_id
        response = self.client("/subscription/aaaa/1234")
        # it throws a NotFound error
        self.assertEqual(response.status_code, STATUS_CODE_NOT_FOUND_ERROR)

    def test_website_form_render__with_product_wrong_subscription_mode_and_company(
        self,
    ):
        # given http_client
        # when we call for the single subscription form page
        # with wrong subscription_mode and company_ext_id
        response = self.client(
            "/subscription/aaaa/1234/{}".format(COMMUNITY_1_SHARE_1_EXT_ID)
        )
        # it throws a NotFound error
        self.assertEqual(response.status_code, STATUS_CODE_NOT_FOUND_ERROR)

    def test_website_form_render__with_product_wrong_company(self):
        # given http_client
        # when we call for the single subscription form page
        # with wrong company_ext_id
        response = self.client(
            "/subscription/member/1234/{}".format(COMMUNITY_1_SHARE_1_EXT_ID)
        )
        # it throws a NotFound error
        self.assertEqual(response.status_code, STATUS_CODE_NOT_FOUND_ERROR)

    def test_website_form_render__with_product_wrong_subscription_mode(self):
        # given http_client
        # when we call for the single subscription form page
        # with wrong subscription_mode
        response = self.client(
            "/subscription/aaaa/{}/{}".format(
                COMMUNITY_1_EXT_ID, COMMUNITY_1_SHARE_1_EXT_ID
            )
        )
        # it throws a NotFound error
        self.assertEqual(response.status_code, STATUS_CODE_NOT_FOUND_ERROR)

    def test_website_form_render__with_wrong_product_wrong_company_and_subscription_mode(
        self,
    ):
        # given http_client
        # when we call for the single subscription form page
        # with wrong subscription_mode, company_ext_id and product_ext_id
        response = self.client("/subscription/aaaa/1234/5678")
        # it throws a NotFound error
        self.assertEqual(response.status_code, STATUS_CODE_NOT_FOUND_ERROR)

    def test_website_form_render__with_wrong_product_wrong_subscription_mode(self):
        # given http_client
        # when we call for the single subscription form page
        # with wrong subscription_mode and product_ext_id
        response = self.client("/subscription/aaa/{}/5678".format(COMMUNITY_1_EXT_ID))
        # it throws a NotFound error
        self.assertEqual(response.status_code, STATUS_CODE_NOT_FOUND_ERROR)

    def test_website_form_render__with_wrong_product_wrong_company(self):
        # given http_client
        # when we call for the single subscription form page
        # with wrong company_ext_id and product_ext_id
        response = self.client("/subscription/member/1234/5678")
        # it throws a NotFound error
        self.assertEqual(response.status_code, STATUS_CODE_NOT_FOUND_ERROR)

    def test_website_form_render__with_wrong_product(self):
        # given http_client
        # when we call for the single subscription form page
        # with wrong product_ext_id
        response = self.client(
            "/subscription/member/{}/5678".format(COMMUNITY_1_EXT_ID)
        )
        # it throws a NotFound error
        self.assertEqual(response.status_code, STATUS_CODE_NOT_FOUND_ERROR)

    # Product must belong to defined company
    def test_website_form_render_wrong_consistency_between_product_and_company(self):
        # given http_client
        # when we call for the single subscription form page
        # for company 2 and a product of company 1
        response = self.client(
            "/subscription/member/{}/{}".format(
                COMMUNITY_2_EXT_ID, COMMUNITY_1_SHARE_1_EXT_ID
            )
        )
        # it throws a NotAcceptable error
        self.assertEqual(response.status_code, STATUS_CODE_CONSISTENCY_ERROR)

    # Product doesn't belong to defined category
    def test_website_form_render_wrong_consistency_between_product_and_category(self):
        # given http_client
        # when we call for the single subscription form page
        # for a product of company 1 with wrong product_categ
        self.env.ref(COMMUNITY_1_SHARE_2_XML_ID).write(
            {
                "categ_id": self.env.ref(
                    "energy_communities_cooperator.product_category_company_voluntary_share"
                )
            }
        )
        response = self.client(
            "/subscription/member/{}/{}".format(
                COMMUNITY_1_EXT_ID, COMMUNITY_1_SHARE_2_EXT_ID
            )
        )
        # it throws a NotAcceptable error
        self.assertEqual(response.status_code, STATUS_CODE_CONSISTENCY_ERROR)

    # Product is not for individuals request on member,invited subscription_mode
    def test_website_form_render_wrong_consistency_with_product_by_individual(self):
        # given http_client
        # when we call for the single subscription form page
        # for a product of company 1 with wrong by_individual flag
        self.env.ref(COMMUNITY_1_SHARE_2_XML_ID).write({"by_individual": False})
        # case member
        response = self.client(
            "/subscription/member/{}/{}".format(
                COMMUNITY_1_EXT_ID, COMMUNITY_1_SHARE_2_EXT_ID
            )
        )
        # it throws a NotAcceptable error
        self.assertEqual(response.status_code, STATUS_CODE_CONSISTENCY_ERROR)
        # case invited
        response = self.client(
            "/subscription/invited/{}/{}".format(
                COMMUNITY_1_EXT_ID, COMMUNITY_1_SHARE_2_EXT_ID
            )
        )
        # it throws a NotAcceptable error
        self.assertEqual(response.status_code, STATUS_CODE_CONSISTENCY_ERROR)

    # Product is not for companies request on member_company,invited_company subscription_mode
    def test_website_form_render_wrong_consistency_with_product_by_company(self):
        # given http_client
        # when we call for the single subscription form page
        # for a product of company 1 with wrong by_company flag
        self.env.ref(COMMUNITY_1_SHARE_2_XML_ID).write({"by_company": False})
        # case member
        response = self.client(
            "/subscription/company_member/{}/{}".format(
                COMMUNITY_1_EXT_ID, COMMUNITY_1_SHARE_2_EXT_ID
            )
        )
        # it throws a NotAcceptable error
        self.assertEqual(response.status_code, STATUS_CODE_CONSISTENCY_ERROR)
        # case invited
        response = self.client(
            "/subscription/company_invited/{}/{}".format(
                COMMUNITY_1_EXT_ID, COMMUNITY_1_SHARE_2_EXT_ID
            )
        )
        # it throws a NotAcceptable error
        self.assertEqual(response.status_code, STATUS_CODE_CONSISTENCY_ERROR)

    # Product is not a share
    def test_website_form_render_wrong_consistency_with_product_is_share(self):
        # given http_client
        # when we call for the single subscription form page
        # for a product of company 1 with wrong is_share flag
        self.env.ref(COMMUNITY_1_SHARE_2_XML_ID).write({"is_share": False})
        response = self.client(
            "/subscription/member/{}/{}".format(
                COMMUNITY_1_EXT_ID, COMMUNITY_1_SHARE_2_EXT_ID
            )
        )
        # it throws a NotAcceptable error
        self.assertEqual(response.status_code, STATUS_CODE_CONSISTENCY_ERROR)

    # Product not available on single form
    def test_website_form_render_single_wrong_consistency_with_product_not_available(
        self,
    ):
        # given http_client
        # when we call for the single subscription form page
        # for a non_available product of company 1
        self.env.ref(COMMUNITY_1_SHARE_2_XML_ID).write(
            {"activate_form_specific_products": False}
        )
        response = self.client(
            "/subscription/member/{}/{}".format(
                COMMUNITY_1_EXT_ID, COMMUNITY_1_SHARE_2_EXT_ID
            )
        )
        # it throws a Locked error
        self.assertEqual(response.status_code, STATUS_CODE_UNAVAILABLE_ERROR)

    # Product not available on generic form
    @patch(
        "odoo.addons.energy_communities_cooperator.controllers.website_share_subscription_controller.WebsiteShareSubscriptionController._get_page_products_dict"
    )
    def test_website_form_render_generic_wrong_consistency_with_product_not_available(
        self, patcher
    ):
        # given http_client
        # when we call for the global subscription form page
        # for a non_available product of company 1
        test_product = self.env.ref(COMMUNITY_1_SHARE_2_XML_ID)
        test_product.write({"display_on_website": False})
        patcher.return_value = {"products": test_product, "product": test_product}
        response = self.client("/subscription/member/{}".format(COMMUNITY_1_EXT_ID))
        # it throws a Locked error
        self.assertEqual(response.status_code, STATUS_CODE_UNAVAILABLE_ERROR)

    def test_website_form_render_member_ok(self):
        # given http_client
        # and a valid data
        # when we call for the global subscription form page
        response = self.client("/subscription/member/{}".format(COMMUNITY_1_EXT_ID))
        # it correctly renders the page
        self.assertEqual(response.status_code, 200)
        # TODO: there are 2 products defined bu Share A is the default one

    def test_website_form_render_member_with_product_ok(self):
        # given http_client
        # and a valid data
        # when we call for the single subscription form page
        response = self.client(
            "/subscription/member/{}/{}".format(
                COMMUNITY_1_EXT_ID, COMMUNITY_1_SHARE_1_EXT_ID
            )
        )
        # it correctly renders the page
        self.assertEqual(response.status_code, 200)

    def test_website_form_member_submission_ok(self):
        # given http_client
        # and a valid data
        # when we submit the form
        SUBSCRIPTION_FORM_SUBMISSION["share_product_id"] = self.env.ref(
            COMMUNITY_1_SHARE_1_XML_ID
        ).id
        # SUBSCRIPTION_FORM_SUBMISSION["csrf_token"] = Request.csrf_token(Request._get_session_and_dname())
        response = self.client(
            "/subscription/member/{}".format(COMMUNITY_1_EXT_ID),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=SUBSCRIPTION_FORM_SUBMISSION,
        )
        # it correctly renders the page
        self.assertEqual(response.status_code, 200)

    def test_website_form_company_member_submission_ok(self):
        # given http_client
        # and a valid data
        # when we submit the form
        SUBSCRIPTION_FORM_SUBMISSION_COMPANY_MEMBER["share_product_id"] = self.env.ref(
            COMMUNITY_1_SHARE_1_XML_ID
        ).id
        response = self.client(
            "/subscription/company_member/{}".format(COMMUNITY_1_EXT_ID),
        )
        # it correctly renders the page
        self.assertEqual(response.status_code, 200)
