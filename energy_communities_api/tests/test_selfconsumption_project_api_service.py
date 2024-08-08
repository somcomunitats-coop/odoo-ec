from functools import partial

import requests

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, tagged

from odoo.addons.base_rest.tests.common import RegistryMixin

from .data import client_data, server_auth_url


@tagged("-at_install", "post_install")
class TestSelfConsumptionApiService(HttpCase, RegistryMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpRegistry()

    def setUp(self):
        super().setUp()
        self.community_id = "3"
        self.timeout = 600
        self.client = partial(self.url_open, timeout=self.timeout)

    @property
    def token(self):
        return self.env.ref("energy_communities_api.apikey_provider").key

    def test__get_selfconsumption_projects__paginated__ok(self) -> None:
        # given http_client
        # self.url_open
        # and a valid token
        # self.token

        # when we call for the list of projects with pagination
        response = self.client(
            "/api/energy-selfconsumption/projects?page=1&page_size=20",
            headers={"API-KEY": self.token},
        )
        self.assertEqual(response.status_code, 200)

    def test__get_selfconsumption_projects__ok(self) -> None:
        # given http_client
        # self.url_open
        # and a valid token
        # self.token

        # when we call for the list of projects without pagination
        response = self.client(
            "/api/energy-selfconsumption/projects",
            headers={"API-KEY": self.token},
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)

    def test__get_selfconsumption_projects_by_cau__ok(self) -> None:
        pass
        # with self._create_test_client() as test_client:
        #     respose: Response = test_client.get(
        #         "projects/001ES0397277816188340VL", headers={"api-token": "12345"}
        #     )

        # self.assertEqual(respose.status_code, status.HTTP_200_OK)
