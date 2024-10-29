from functools import partial

import requests

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, tagged

from odoo.addons.base_rest.tests.common import RegistryMixin

try:
    from .data import client_data, server_auth_url
except:
    pass


@tagged("-at_install", "post_install")
class TestSelfConsumptionApiService(HttpCase, RegistryMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpRegistry()

    def setUp(self):
        super().setUp()
        self.maxDiff = None
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
        # given http_client
        # self.client
        # and a valid token
        # self.token

        # when we call for a specific project
        response = self.client(
            "/api/energy-selfconsumption/projects/ES1234123456789012JY1FA000",
            headers={"API-KEY": self.token},
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)

    def test__get_selfconsumption_projects_by_cau__project_not_found(self) -> None:
        # given http_client
        # self.client
        # and a valid token
        # self.token

        # when we call for a specific project
        response = self.client(
            "/api/energy-selfconsumption/projects/ES12341234567890A000",
            headers={"API-KEY": self.token},
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 404)
        self.assertDictEqual(response.json(), {"code": 404, "name": "Not Found"})

    def test__get_selfconsumption_project_members__ok(self) -> None:
        # given http_client
        # self.client
        # and a valid token
        # self.token

        # when we call for the members of a project
        response = self.client(
            "/api/energy-selfconsumption/projects/ES1234123456789012JY1FA000/members",
            headers={"API-KEY": self.token},
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
