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
        # and an energy community
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

    def test__communities_communities_services__detail_ok(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token
        # and an energy community
        community_1_id = self.community_id
        # and a service of that community
        service_id = community_data["service_id"]

        # when we call for the detail of that service
        response = self.client(
            f"/api/communities/community/community_services/{service_id}",
            headers={"Authorization": self.token, "CommunityId": community_1_id},
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and the datail of that service
        self.assertDictEqual(response.json()["data"], community_data["service_info"])

    def test__communities_communities_services__detail_open_inscriptions(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token
        # and an energy community
        community_1_id = self.community_id
        # and a service of that community that has open inscriptions
        service_id = community_data["service_id"]

        # when we call for the detail of that service
        response = self.client(
            f"/api/communities/community/community_services/{service_id}",
            headers={"Authorization": self.token, "CommunityId": community_1_id},
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and inscriptions are open
        self.assertTrue(response.json()["data"]["open_inscriptions"])
        # and also there is an url_form
        self.assertNotEqual(response.json()["data"]["inscriptions_url_form"], "")

    def test__communities_communities_services__service_not_found(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token
        # and an energy community
        community_1_id = self.community_id
        # and an undefined service
        service_id = 453678

        # when we call for the detail of that service
        response = self.client(
            f"/api/communities/community/community_services/{service_id}",
            headers={"Authorization": self.token, "CommunityId": community_1_id},
        )
        # then we obtain a 404 response code
        self.assertEqual(response.status_code, 404)
        # and a not found response
        self.assertDictEqual(response.json(), {"code": 404, "name": "Not Found"})

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

    def test__community_service_metrics__ok(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token
        # and energy_community
        community_1_id = self.community_id
        # and a community service
        service_id = community_data["service_id"]
        # and a range of dates
        from_date = date(2024, 1, 1)
        to_date = date(2024, 12, 31)

        # when we call for the metrics of that service that offer the community
        response = self.client(
            f"/api/communities/community/community_services/{service_id}/metrics?from_date={from_date}&to_date={to_date}",
            headers={"Authorization": self.token, "CommunityId": community_1_id},
        )

        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and its metrics information
        self.assertDictEqual(response.json()["data"], community_data["service_metrics"])

    def test__community_service_metrics__without_monitoring_provider(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token
        # and energy_community
        community_1_id = self.community_id
        # and a community service without a monitoring provider
        service_id = community_data["service_id_whithout_provider"]
        # and a range of dates
        from_date = date(2024, 1, 1)
        to_date = date(2024, 12, 31)

        # when we call for the metrics of that service
        response = self.client(
            f"/api/communities/community/community_services/{service_id}/metrics?from_date={from_date}&to_date={to_date}",
            headers={"Authorization": self.token, "CommunityId": community_1_id},
        )

        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and data is empty
        self.assertIsNone(response.json()["data"])

    def test__community_service_energy_production__ok(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token
        # and energy_community
        # self.community_id
        # and a community service
        service_id = community_data["service_id"]
        # and a range of dates
        from_date = date(2024, 1, 1)
        to_date = date(2024, 12, 31)

        # when we call for the production of that community service
        url = f"/api/communities/community/community_services/{service_id}/metrics/energy_production?from_date={from_date}&to_date={to_date}"
        response = self.client(
            url,
            headers={
                "Authorization": self.token,
                "CommunityId": self.community_id,
            },
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and the production
        response = response.json()
        self.assertGreaterEqual(response["count"], 1)

    def test__community_services_energy_selfconsumption__ok(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token
        # and energy_community
        # self.community_id
        # and a community service
        service_id = community_data["service_id"]
        # and a range of dates
        from_date = date(2024, 1, 1)
        to_date = date(2024, 12, 31)

        # when we call for the selfconsumption of that community service
        url = f"/api/communities/community/community_services/{service_id}/metrics/energy_selfconsumption?from_date={from_date}&to_date={to_date}"
        response = self.client(
            url,
            headers={
                "Authorization": self.token,
                "CommunityId": self.community_id,
            },
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and the selfconsumed energy
        response = response.json()
        self.assertGreaterEqual(response["count"], 1)

    def test__community_services_energy_exported__ok(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token
        # and energy_community
        # self.community_id
        # and a community service
        service_id = community_data["service_id"]
        # and a range of dates
        from_date = date(2024, 1, 1)
        to_date = date(2024, 12, 31)

        # when we call for the selfconsumption of that community service
        url = f"/api/communities/community/community_services/{service_id}/metrics/energy_exported?from_date={from_date}&to_date={to_date}"
        response = self.client(
            url,
            headers={
                "Authorization": self.token,
                "CommunityId": self.community_id,
            },
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and the selfconsumed energy
        response = response.json()
        self.assertGreaterEqual(response["count"], 1)

    def test__community_services_energy_comsumption__ok(self):
        # given http_client
        # self.url_open
        # and a valid token
        # self.token
        # and energy_community
        # self.community_id
        # and a community service
        service_id = community_data["service_id"]
        # and a range of dates
        from_date = date(2024, 1, 1)
        to_date = date(2024, 12, 31)

        # when we call for the selfconsumption of that community service
        url = f"/api/communities/community/community_services/{service_id}/metrics/energy_consumption?from_date={from_date}&to_date={to_date}"
        response = self.client(
            url,
            headers={
                "Authorization": self.token,
                "CommunityId": self.community_id,
            },
        )
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and the selfconsumed energy
        response = response.json()
        self.assertGreaterEqual(response["count"], 1)
