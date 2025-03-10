from datetime import date
from functools import partial

import requests

from odoo.tests import HttpCase, tagged

from odoo.addons.base_rest.tests.common import RegistryMixin

from ..schemas import EnergyCommunityInfo

try:
    from .data import client_data, community_data, server_auth_url
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
        self.community_id = community_data["community_id"]
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
            "/api/communities/community/",
            headers={"Authorization": self.token, "CommunityId": community_1_id},
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and a correct content
        self.assertIsInstance(
            EnergyCommunityInfo(**response.json()["data"]), EnergyCommunityInfo
        )

    def test__communities_communities_services__ok(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token
        # a member belonging into a energy_community
        community_1_id = self.community_id

        # when we call for the energy services that offers that community
        response = self.client(
            "/api/communities/community/community_services",
            headers={"Authorization": self.token, "CommunityId": community_1_id},
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and at least one community service
        self.assertGreaterEqual(len(response.json()["data"]), 1)

    def test__communities_communities_services__with_paging_ok(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token
        # a member belonging into a energy_community
        community_1_id = self.community_id
        page_size = 1

        # when we call for the energy services that offers that community
        response = self.client(
            f"/api/communities/community/community_services?page_size={page_size}",
            headers={"Authorization": self.token, "CommunityId": community_1_id},
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and one community service
        self.assertEqual(len(response.json()["data"]), 1)
        # and no previous url but yes a next url
        self.assertIsNone(response.json()["links"]["previous_page"])
        self.assertIn(
            "/api/communities/community/community_services?page_size=1&page=2",
            response.json()["links"]["next_page"],
        )

    def test__communities_communities_services_metrics__ok(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token
        # a member belonging into a energy_community
        community_1_id = self.community_id
        # and a range of dates
        from_date = date(2024, 1, 1)
        to_date = date(2024, 12, 31)

        # when we call for the metrics of the energy services that offers that community between that two dates
        response = self.client(
            f"/api/communities/community/community_services/metrics?from_date={from_date}&to_date={to_date}",
            headers={"Authorization": self.token, "CommunityId": community_1_id},
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and at least one community service

        self.assertGreaterEqual(len(response.json()["data"]), 1)
