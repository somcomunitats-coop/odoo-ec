from datetime import date
from unittest.mock import patch

from odoo.addons.component.core import WorkContext
from odoo.addons.component.tests.common import TransactionComponentCase

from ..components import PartnerApiInfo, ProjectApiInfo
from ..components.opendata_api_info import OpenDataApiInfo
from ..schemas import (
    CommunityInfo,
    CommunityServiceInfo,
    CommunityServiceMetricsInfo,
    EnergyPoint,
    MemberInfo,
    NetworkInfo,
    PaginationLimits,
)

try:
    from .data import client_data
except:
    pass


class TestMemberApiInfo(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.backend = self.env["api.info.backend"].browse(1)

    def test__get_member_info(self):
        # given a energy community member
        # member = self.env.ref("cooperator.res_partner_cooperator_1_demo")
        member = self.env["res.partner"].search([("vat", "=", client_data["username"])])
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
                CommunityInfo.from_orm(community)
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
        service_id = 32
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


class TestProjectApiInfo(TransactionComponentCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.backend = self.env["api.info.backend"].browse(1)
        self.active_project_domain = lambda partner: [
            ("partner_id", "=", partner.id),
            ("project_id.state", "=", "active"),
        ]
        self.project_work_context = WorkContext(
            "energy_project.project",
            collection=self.backend,
            schema_class=EnergyPoint,
        )

    def test__get_project_daily_production(self):
        # given a energy community member
        # member = self.env.ref("cooperator.res_partner_cooperator_1_demo")
        member = self.env["res.partner"].search([("vat", "=", client_data["username"])])
        # a project
        project = (
            self.env["energy_project.inscription"]
            .search(self.active_project_domain(member))
            .mapped(lambda inscription: inscription.project_id)
        )[0]
        # a range of dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # given a api info component
        component = self.project_work_context.component(usage="api.info")
        self.assertIsInstance(component, ProjectApiInfo)

        # when we ask for the daily energy production of a project in which the member is involv
        # between two dates
        daily_production = component.get_project_daily_production(
            project, member, date_from, date_to
        )

        # then we obtain the daily production of the member between that dates
        self.assertGreaterEqual(
            len(daily_production),
            1,
        )

    def test__get_project_daily_selfconsumption(self):
        # given a energy community member
        # member = self.env.ref("cooperator.res_partner_cooperator_1_demo")
        member = self.env["res.partner"].search([("vat", "=", client_data["username"])])
        # a project
        project = (
            self.env["energy_project.inscription"]
            .search(self.active_project_domain(member))
            .mapped(lambda inscription: inscription.project_id)
        )[0]
        # a range of dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # given a api info component
        component = self.project_work_context.component(usage="api.info")
        self.assertIsInstance(component, ProjectApiInfo)

        # when we ask for the daily energy selfconumption of the member in that project
        # between two dates
        daily_selfconsumption = component.get_project_daily_selfconsumption(
            project, member, date_from, date_to
        )

        # then we obtain the daily production of the member between that dates
        self.assertGreaterEqual(
            len(daily_selfconsumption),
            1,
        )

    def test__get_project_daily_exported_energy(self):
        # given a energy community member
        # member = self.env.ref("cooperator.res_partner_cooperator_1_demo")
        member = self.env["res.partner"].search([("vat", "=", client_data["username"])])
        # a project
        project = (
            self.env["energy_project.inscription"]
            .search(self.active_project_domain(member))
            .mapped(lambda inscription: inscription.project_id)
        )[0]
        # a range of dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # given a api info component
        component = self.project_work_context.component(usage="api.info")
        self.assertIsInstance(component, ProjectApiInfo)

        # when we ask for the daily exported energy of the member in that project
        # between two dates
        exported_energy = component.get_project_daily_exported_energy(
            project, member, date_from, date_to
        )

        # then we obtain the daily production of the member between that dates
        self.assertGreaterEqual(
            len(exported_energy),
            1,
        )

    def test__get_project_daily_consumed_energy(self):
        # given a energy community member
        # member = self.env.ref("cooperator.res_partner_cooperator_1_demo")
        member = self.env["res.partner"].search([("vat", "=", client_data["username"])])
        # a project
        project = (
            self.env["energy_project.inscription"]
            .search(self.active_project_domain(member))
            .mapped(lambda inscription: inscription.project_id)
        )[0]
        # a range of dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # given a api info component
        component = self.project_work_context.component(usage="api.info")
        self.assertIsInstance(component, ProjectApiInfo)

        # when we ask for the daily consumed energy of the member in that project
        # between two dates
        exported_energy = component.get_project_daily_consumed_energy(
            project, member, date_from, date_to
        )

        # then we obtain the daily production of the member between that dates
        self.assertGreaterEqual(
            len(exported_energy),
            1,
        )


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
