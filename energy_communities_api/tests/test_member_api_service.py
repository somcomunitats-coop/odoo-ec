import requests

from odoo.tests import HttpCase, tagged

from odoo.addons.base_rest.tests.common import RegistryMixin

from .data import client_data, client_data_response, server_auth_url


@tagged("-at_install", "post_install")
class TestMemberApiService(HttpCase, RegistryMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpRegistry()

    def setUp(self):
        super().setUp()
        self.maxDiff = None

    @property
    def token(self):
        if not hasattr(self, "_token"):
            data = client_data
            response = requests.post(server_auth_url, data=data)
            self._token = response.json().get("access_token")

        return f"Bearer {self._token}"

    def test__me_endpoint__ok(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token

        # when we call for the personal data in api
        response = self.url_open(
            "/api/energy-communities/me", headers={"Authorization": self.token}
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and we get the correct information
        self.assertDictEqual(
            response.json(),
            {
                "data": client_data_response,
                "links": {"self_": "http://127.0.0.1:8069/api/energy-communities/me"},
            },
        )

    def test__me_communities_endpoint__ok(self):
        # given http_client
        # self.url_open
        # and a valid personal token
        # self.token

        # when we call for the energy_communties that i belong
        response = self.url_open(
            "/api/energy-communities/me/communities",
            headers={"Authorization": self.token},
        )

        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and we get the correct information
        communities = response.json()
        self.assertGreaterEqual(len(communities.get("data", 0)), 1)
        self.assertEqual(
            communities.get("links", {}).get("self", ""),
            "http://127.0.0.1:8069/api/energy-communities/me/communities",
        )
