from unittest.mock import patch

from odoo.addons.component.core import WorkContext
from odoo.addons.component.tests.common import TransactionComponentCase

from ..components.partner_api_info import PartnerApiInfo
from ..schemas import CommunityInfo, MemberInfo, PaginationLimits


class TestMemberApiInfo(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.backend = self.env["api.info.backend"].browse(1)

    def test__get_member_info(self):
        # given a energy community member
        member = self.env.ref("cooperator.res_partner_cooperator_1_demo")
        # given a api info component
        work = WorkContext(
            "res.partner", collection=self.backend, schema_class=MemberInfo
        )
        api_info_component = work.component(usage="api.info")
        self.assertIsInstance(api_info_component, PartnerApiInfo)

        # when we ask for the information of a member
        member_info = api_info_component.get_member_info(member)

        # then we have the information related whit that partner
        self.assertDictEqual(
            member_info.dict(),
            {
                "email": "virginie@demo.net",
                "lang": "en_US",
                "name": "Virginie Leloup",
                "member_number": "0",
            },
        )
        self.assertIsInstance(member_info, MemberInfo)

    @patch(
        "odoo.addons.energy_communities_api.components.partner_api_info.PartnerApiInfo._get_communities"
    )
    def test__get_member_communities(self, patcher):
        def fake_energy_communities():
            return [self.env["res.company"].browse(id_) for id_ in range(1, 3)]

        patcher.return_value = fake_energy_communities()

        # given a energy community member
        member = self.env.ref("cooperator.res_partner_cooperator_1_demo")
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
                CommunityInfo.from_orm(community)
                for community in fake_energy_communities()
            ],
        )

    def test__get_member_communities_paging_params(self):  # , patcher):
        def fake_energy_communities():
            return [self.env["res.company"].browse(id_) for id_ in range(1, 3)]

        # given a energy community member
        member = self.env.ref("cooperator.res_partner_cooperator_1_demo")
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
