from datetime import date
from unittest.mock import patch

from odoo.addons.component.core import WorkContext
from odoo.addons.component.tests.common import TransactionComponentCase

from ...components import PartnerApiInfo
from ...schemas import (
    CommunityInfo,
    CommunityServiceInfo,
    CommunityServiceMetricsInfo,
    MemberInfo,
    PaginationLimits,
)

try:
    from ..data import client_data, client_data_response, community_data
except:
    pass


class TestMemberApiInfo(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.community_id = int(community_data["community_id"])
        self.backend = (
            self.env["api.info.backend"].with_company(self.community_id).browse(1)
        )

    def test__get_member_info(self):
        # given a energy community member
        member = (
            self.env["res.partner"]
            .with_company(self.community_id)
            .search([("vat", "=", client_data["username"])])
        )
        # given a api info component
        work = WorkContext(
            "res.partner", collection=self.backend, schema_class=MemberInfo
        )
        api_info_component = work.component(usage="api.info")
        self.assertIsInstance(api_info_component, PartnerApiInfo)

        # when we ask for the information of a member
        member_info = api_info_component.get_member_info(member)

        # then we have the information related whit that partner
        self.assertDictEqual(member_info.model_dump(), client_data_response)
        self.assertIsInstance(member_info, MemberInfo)

    @patch(
        "odoo.addons.energy_communities_api.components.partner_api_info.PartnerApiInfo._get_communities"
    )
    def test__get_member_communities(self, patcher):
        def fake_energy_communities():
            return [self.env["res.company"].browse(id_) for id_ in range(1, 3)]

        patcher.return_value = fake_energy_communities()

        # given a energy community member
        # member = self.env.ref("cooperator.res_partner_cooperator_1_demo")
        member = self.env["res.partner"].search([("vat", "=", client_data["username"])])
        # given a api info component
        work = WorkContext(
            "res.partner", collection=self.backend, schema_class=CommunityInfo
        )
        api_info_component = work.component(usage="api.info")
        self.assertIsInstance(api_info_component, PartnerApiInfo)

        # when we ask for the energy_communities that this member belongs
        member_communities = api_info_component.get_member_communities(member)

        # then we have that communities
        self.assertListEqual(
            member_communities,
            [
                CommunityInfo.model_validate(community)
                for community in fake_energy_communities()
            ],
        )

    def test__get_member_communities_paging_params(self):  # , patcher):
        # given a energy community member
        # member = self.env.ref("cooperator.res_partner_cooperator_1_demo")
        member = self.env["res.partner"].search([("vat", "=", client_data["username"])])
        # given a paging object for 1 element and an api info component
        page = 1
        page_size = 1
        paging = PaginationLimits(
            limit=page_size, offset=(page - 1) * page_size, page=page
        )
        work = WorkContext(
            "res.partner",
            collection=self.backend,
            schema_class=CommunityInfo,
            paging=paging,
        )
        api_info_component = work.component(usage="api.info")

        # when we ask for the energy_communities that this member belongs
        member_communities = api_info_component.get_member_communities(member)

        # then we have 1 communities
        self.assertEqual(
            len(member_communities),
            1,
        )

    def test__get_member_community_services_metrics(self):
        # given a energy community member
        # member = self.env.ref("cooperator.res_partner_cooperator_1_demo")
        member = self.env["res.partner"].search([("vat", "=", client_data["username"])])
        # a range of dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # given a api info component
        work = WorkContext(
            "res.partner",
            collection=self.backend,
            schema_class=CommunityServiceMetricsInfo,
        )
        api_info_component = work.component(usage="api.info")
        self.assertIsInstance(api_info_component, PartnerApiInfo)

        # when we ask for the metrics of the services that this member is involved between two dates
        member_community_services_metrics = (
            api_info_component.get_member_community_services_metrics(
                member, date_from, date_to
            )
        )

        # then we obtain all metrics of those services
        self.assertGreaterEqual(
            len(member_community_services_metrics),
            1,
        )

    def test__get_member_community_services(self):
        # given a energy community member
        # member = self.env.ref("cooperator.res_partner_cooperator_1_demo")
        member = self.env["res.partner"].search([("vat", "=", client_data["username"])])
        # given a api info component
        work = WorkContext(
            "res.partner",
            collection=self.backend,
            schema_class=CommunityServiceInfo,
        )
        api_info_component = work.component(usage="api.info")
        self.assertIsInstance(api_info_component, PartnerApiInfo)

        # when we ask for the services that this member is involved
        member_community_services = api_info_component.get_member_community_services(
            member
        )

        # then we obtain all services in which that member has an inscription
        self.assertGreaterEqual(
            len(member_community_services),
            1,
        )

    def test__get_member_community_service_detail(self):
        # given a energy community member
        # member = self.env.ref("cooperator.res_partner_cooperator_1_demo")
        member = self.env["res.partner"].search([("vat", "=", client_data["username"])])
        # given an id of a community service
        service_id = community_data["service_id"]
        # given a api info component
        work = WorkContext(
            "res.partner",
            collection=self.backend,
            schema_class=CommunityServiceInfo,
            community_id=member.company_id,
        )
        api_info_component = work.component(usage="api.info")
        self.assertIsInstance(api_info_component, PartnerApiInfo)

        # when we ask for the services that this member is involved
        community_service = api_info_component.get_member_community_service_detail(
            member, service_id
        )

        # then we obtain the corresponding community service
        self.assertIsInstance(community_service, CommunityServiceInfo)
