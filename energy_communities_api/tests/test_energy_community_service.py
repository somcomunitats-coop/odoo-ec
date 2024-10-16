from functools import partial

import requests

from odoo.tests import HttpCase, tagged

from odoo.addons.base_rest.tests.common import RegistryMixin

from ..schemas import EnergyCommunityInfo

try:
    from .data import client_data, server_auth_url
except ImportError:
    pass


@tagged("-at_install", "post_install")
class TestEnergyCommunityApiService(HttpCase, RegistryMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpRegistry()

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.community_id = "55"
        self.timeout = 600
        self.client = partial(self.url_open, timeout=self.timeout)

    @property
    def token(self):
        if not hasattr(self, "_token"):
            data = client_data
            response = requests.post(server_auth_url, data=data)
            self._token = response.json().get("access_token")

        return f"Bearer {self._token}"

    def test__communities_endpoint__ok(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token
        # a member belonging to two energy communities

        community_1_id = self.community_id

        # when we call for the information if his/her community
        response = self.client(
            f"/api/communities/communities/{community_1_id}",
            headers={"Authorization": self.token, "CommunityId": community_1_id},
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and a correct content
        self.assertIsInstance(
            EnergyCommunityInfo(**response.json()["data"]), EnergyCommunityInfo
        )
