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

    @property
    def token(self):
        if not hasattr(self, "_token"):
            data = client_data
            response = requests.post(server_auth_url, data=data)
            self._token = response.json().get("access_token")

        return f"Bearer {self._token}"

    def test__get_selfconsumption_projects__ok(self) -> None:
        # given http_client
        # self.url_open
        # and a valid token
        # self.token

        # when we call for the list of projects with pagination or without
        # paged_response = self.url_open(
        #     "/api/energy-selfconsumption/projects?page=1&page_size=20",
        #     headers={"Authorization": self.token},
        #     timeout=self.timeout,
        # )
        response = self.url_open(
            "/api/energy-selfconsumption/projects",
            headers={"Authorization": self.token},
            timeout=self.timeout,
        )
        # then we obtain a 200 response code
        # self.assertEqual(paged_response.status_code, 200)
        self.assertEqual(response.status_code, 200)

    def test__get_selfconsumption_projects_by_cau__ok(self) -> None:
        pass
        # with self._create_test_client() as test_client:
        #     respose: Response = test_client.get(
        #         "projects/001ES0397277816188340VL", headers={"api-token": "12345"}
        #     )

        # self.assertEqual(respose.status_code, status.HTTP_200_OK)
