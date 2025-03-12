from datetime import date

from odoo.addons.component.core import WorkContext
from odoo.addons.component.tests.common import TransactionComponentCase

from ...components import ProjectApiInfo
from ...schemas import EnergyPoint

try:
    from ..data import client_data
except:
    pass


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
        daily_production = component.get_project_daily_production_by_member(
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
        daily_selfconsumption = component.get_project_daily_selfconsumption_by_member(
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
        exported_energy = component.get_project_daily_exported_energy_by_member(
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
        exported_energy = component.get_project_daily_consumed_energy_by_member(
            project, member, date_from, date_to
        )

        # then we obtain the daily production of the member between that dates
        self.assertGreaterEqual(
            len(exported_energy),
            1,
        )
