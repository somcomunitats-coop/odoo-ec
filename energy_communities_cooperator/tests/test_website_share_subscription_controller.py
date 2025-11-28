from functools import partial

import requests

import odoo
from odoo.tests.common import HttpCase, tagged

from odoo.addons.base_rest.tests.common import RegistryMixin

# HOST = "localhost"
# PORT = odoo.tools.config["http_port"]


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
        self.client = partial(self.url_open, timeout=self.timeout)

    def test_website_form_render__wrong_subscription_mode(self):
        # given http_client
        # self.url_open
        # and a valid data
        # when we call for the global subscription form page
        response = self.client(
            "/subscription/aaaa/ac3478d69a3c81fa62e60f5c3696165a4e5e6ac4"
        )
        # it throws a 404 exception and renders 404 page
        self.assertEqual(response.status_code, 404)

    def test_website_form_render__wrong_company(self):
        # given http_client
        # self.url_open
        # and a valid data
        # when we call for the global subscription form page
        response = self.client("/subscription/member/1234")
        # it throws a 404 exception and renders 404 page
        self.assertEqual(response.status_code, 404)

    def test_website_form_render__wrong_subscription_mode_and_company(self):
        # given http_client
        # self.url_open
        # and a valid data
        # when we call for the global subscription form page
        response = self.client("/subscription/aaaa/1234")
        # it throws a 404 exception and renders 404 page
        self.assertEqual(response.status_code, 404)

    def test_website_form_render__with_product_wrong_subscription_mode_and_company(
        self,
    ):
        # given http_client
        # self.url_open
        # and a valid data
        # when we call for the global subscription form page
        response = self.client(
            "/subscription/aaaa/1234/7719a1c782a1ba91c031a682a0a2f8658209adbf"
        )
        # it throws a 404 exception and renders 404 page
        self.assertEqual(response.status_code, 404)

    def test_website_form_render__with_product_wrong_company(self):
        # given http_client
        # self.url_open
        # and a valid data
        # when we call for the global subscription form page
        response = self.client(
            "/subscription/member/1234/7719a1c782a1ba91c031a682a0a2f8658209adbf"
        )
        # it throws a 404 exception and renders 404 page
        self.assertEqual(response.status_code, 404)

    def test_website_form_render__with_product_wrong_subscription_mode(self):
        # given http_client
        # self.url_open
        # and a valid data
        # when we call for the global subscription form page
        response = self.client(
            "/subscription/aaaa/ac3478d69a3c81fa62e60f5c3696165a4e5e6ac4/7719a1c782a1ba91c031a682a0a2f8658209adbf"
        )
        # it throws a 404 exception and renders 404 page
        self.assertEqual(response.status_code, 404)

    def test_website_form_render__with_wrong_product_wrong_company_and_subscription_mode(
        self,
    ):
        # given http_client
        # self.url_open
        # and a valid data
        # when we call for the global subscription form page
        response = self.client("/subscription/aaaa/1234/5678")
        # it throws a 404 exception and renders 404 page
        self.assertEqual(response.status_code, 404)

    def test_website_form_render__with_wrong_product_wrong_subscription_mode(self):
        # given http_client
        # self.url_open
        # and a valid data
        # when we call for the global subscription form page
        response = self.client(
            "/subscription/aaa/ac3478d69a3c81fa62e60f5c3696165a4e5e6ac4/5678"
        )
        # it throws a 404 exception and renders 404 page
        self.assertEqual(response.status_code, 404)

    def test_website_form_render__with_wrong_product_wrong_company(self):
        # given http_client
        # self.url_open
        # and a valid data
        # when we call for the global subscription form page
        response = self.client("/subscription/member/1234/5678")
        # it throws a 404 exception and renders 404 page
        self.assertEqual(response.status_code, 404)

    def test_website_form_render__with_wrong_product(self):
        # given http_client
        # self.url_open
        # and a valid data
        # when we call for the global subscription form page
        response = self.client(
            "/subscription/member/ac3478d69a3c81fa62e60f5c3696165a4e5e6ac4/5678"
        )
        # it throws a 404 exception and renders 404 page
        self.assertEqual(response.status_code, 404)

    def test_website_form_render_member_ok(self):
        # given http_client
        # self.url_open
        # and a valid data
        # when we call for the global subscription form page
        response = self.client(
            "/subscription/member/ac3478d69a3c81fa62e60f5c3696165a4e5e6ac4"
        )
        # it correctly renders the page
        self.assertEqual(response.status_code, 200)

    def test_website_form_render_member_with_product_ok(self):
        # given http_client
        # self.url_open
        # and a valid data
        # when we call for the global subscription form page
        response = self.client(
            "/subscription/member/ac3478d69a3c81fa62e60f5c3696165a4e5e6ac4/7719a1c782a1ba91c031a682a0a2f8658209adbf"
        )
        # it correctly renders the page
        self.assertEqual(response.status_code, 200)
