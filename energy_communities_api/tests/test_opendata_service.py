from functools import partial

from odoo.tests import HttpCase, tagged

from odoo.addons.base_rest.tests.common import RegistryMixin


@tagged("-at_install", "post_install")
class TestOpenDataService(HttpCase, RegistryMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpRegistry()

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.timeout = 600
        self.client = partial(self.url_open, timeout=self.timeout)

    def test__network_endpoint__ok(self):
        # given http_client
        # self.url_open

        # when we call for the network opendata information
        response = self.client("/api/opendata/network")
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # a correct response
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "energy_communities_active": 83,
                    "energy_communities_goal": 1110,
                    "energy_communities_total": 528,
                    "inscriptions_in_activation": 445,
                    "members": 3137,
                },
                "links": {
                    "next_page": None,
                    "previous_page": None,
                    "self_": "http://127.0.0.1:8069/api/opendata/network",
                },
            },
        )
