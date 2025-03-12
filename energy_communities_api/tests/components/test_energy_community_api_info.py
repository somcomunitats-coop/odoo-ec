from datetime import date

from odoo.addons.component.core import WorkContext
from odoo.addons.component.tests.common import TransactionComponentCase

from ...components.energy_community_api_info import EnergyCommunityApiInfo
from ...schemas import CommunityServiceInfo

try:
    from ..data import community_data
except:
    pass


class TestEnergyCommunityApiInfo(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.backend = self.env["api.info.backend"].browse(1)

    def test__get_community_services(self):
        # given a energy community
        community_id = int(community_data["community_id"])

        # given a api info component
        work = WorkContext(
            "res.company",
            collection=self.backend,
            schema_class=CommunityServiceInfo,
            paging=None,
        )
        api_info_component = work.component(usage="api.info")
        self.assertIsInstance(api_info_component, EnergyCommunityApiInfo)

        # when we ask for the services that comunity
        community_services = api_info_component.get_community_services(community_id)
        # then we obtain all services of that community
        self.assertGreaterEqual(len(community_services), 1)

    def test__get_community_services_metrics(self):
        # given a energy community
        community_id = int(community_data["community_id"])
        # a range of dates
        date_from = date(2024, 1, 1)
        date_to = date(2024, 12, 31)

        # given a api info component
        work = WorkContext(
            "res.company",
            collection=self.backend,
            schema_class=CommunityServiceInfo,
            paging=None,
        )
        api_info_component = work.component(usage="api.info")
        self.assertIsInstance(api_info_component, EnergyCommunityApiInfo)

        # when we ask for the services that comunity
        community_services_metrics = api_info_component.get_community_services_metrics(
            community_id, date_from, date_to
        )
        # then we obtain all services of that community
        self.assertGreaterEqual(len(community_services_metrics), 1)
