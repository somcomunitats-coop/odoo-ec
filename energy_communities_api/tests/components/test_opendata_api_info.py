from odoo.addons.component.tests.common import TransactionComponentCase

from ...components.opendata_api_info import OpenDataApiInfo
from ...schemas import NetworkInfo


class TestOpenDataApiInfo(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.backend = self.env["api.info.backend"].browse(1)

    def test__get_network_metrics_ok(self):
        # given a OpenDataApiInfo component
        with self.backend.work_on("api.info.backend", schema_class=NetworkInfo) as work:
            opendata_component = work.component(usage="opendata.info")
        self.assertIsInstance(opendata_component, OpenDataApiInfo)

        # when we ask for the network metrics
        network_metrics = opendata_component.get_network_metrics()

        # then we obtain all metrics for network opedata
        self.assertDictEqual(
            network_metrics.dict(),
            {
                "energy_communities_active": 71,
                "energy_communities_goal": 1110,
                "energy_communities_total": 515,
                "inscriptions_in_activation": 444,
                "members": 2401,
            },
        )
        self.assertIsInstance(network_metrics, NetworkInfo)
