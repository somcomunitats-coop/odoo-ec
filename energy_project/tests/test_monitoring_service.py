from datetime import date

from odoo.tests.common import TransactionCase

from ..backends import ArkenovaBackend
from ..backends.domain import MeasurePoint
from ..services import MonitoringService

try:
    from .backends_data import arkenova_data, member_code, project_code
except ImportError:
    pass


class TestMonitoringService(TransactionCase):
    def setUp(self):
        self.maxDiff = None
        self.backend = ArkenovaBackend(**arkenova_data)
        self.monitoring_service = MonitoringService(backend=self.backend)

    def test__create_monitoring_service(self):
        # given a backend that provide valid data
        backend = self.backend

        # when we create an instance of a monitoring service with that backend
        monitoring_service = MonitoringService(backend=backend)

        # then we have an instance of that service
        self.assertIsInstance(monitoring_service, MonitoringService)

    def test__energy_consumption_by_member(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # a member id
        member_id = member_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the consumed_energy for that user
        consumed_energy = self.monitoring_service.energy_consumption_by_member(
            system_id, member_id, date_from, date_to
        )

        # then we obtain the value of the consumed energy between that dates
        self.assertEqual(consumed_energy, 172.123)

    def test__energy_selfconsumption_by_member(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # a member id
        member_id = member_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the selfconsumed_energy for that user
        selfconsumed_energy = self.monitoring_service.energy_selfconsumption_by_member(
            system_id, member_id, date_from, date_to
        )

        # then we obtain the value of the exported energy between that dates
        self.assertEqual(selfconsumed_energy, 94.702)

    def test__energy_gridconsumption_by_member(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # a member id
        member_id = member_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the energy consumed from the grid for that user
        gridconsumption_energy = (
            self.monitoring_service.energy_gridconsumption_by_member(
                system_id, member_id, date_from, date_to
            )
        )

        # then we obtain the value of the energy consumeed from the grid between that dates
        self.assertEqual(gridconsumption_energy, 77.421)

    def test__energy_gridinjection_by_member(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # a member id
        member_id = member_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the exported_energy for that user
        exported_energy = self.monitoring_service.energy_gridinjection_by_member(
            system_id, member_id, date_from, date_to
        )

        # then we obtain the value of the exported energy between that dates
        self.assertEqual(exported_energy, 1101.458)

    def test__energy_production_by_member(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # a member id
        member_id = member_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the generated_energy for that user
        generated_energy = self.monitoring_service.energy_production_by_member(
            system_id, member_id, date_from, date_to
        )

        # then we obtain the value of the generated energy between that dates
        self.assertEqual(generated_energy, 1196.16)

    def test__energy_selfconsumption_ratio_by_member(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # a member id
        member_id = member_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for percentage of energy self-consumed
        selfconsumed_ratio = (
            self.monitoring_service.energy_selfconsumption_ratio_by_member(
                system_id, member_id, date_from, date_to
            )
        )

        # then we obtain the value of the generated energy between that dates
        self.assertEqual(selfconsumed_ratio, 0.0792)

    def test__energy_selfconsumption_surplus_by_member(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # a member id
        member_id = member_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for percentage of energy exported to the energy grid
        surplus_ratio = self.monitoring_service.energy_surplus_ratio_by_member(
            system_id, member_id, date_from, date_to
        )

        # then we obtain the percentage of the energy exported
        self.assertEqual(surplus_ratio, 0.9208)

    def test__relation_energy_selfconsumed_surplus_by_member(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # a member id
        member_id = member_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the percentage of energy exported to the energy grid
        surplus_ratio = self.monitoring_service.energy_surplus_ratio_by_member(
            system_id, member_id, date_from, date_to
        )
        # and we ask for the percentage of energy selfconsumed
        selfconsumed_ratio = (
            self.monitoring_service.energy_selfconsumption_ratio_by_member(
                system_id, member_id, date_from, date_to
            )
        )

        # then the sum must be 1
        self.assertEqual(surplus_ratio + selfconsumed_ratio, 1.0)

    def test__energy_usage_ratio_by_member(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # a member id
        member_id = member_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the percentage of used energy of that member
        energy_usage_ratio = self.monitoring_service.energy_usage_ratio_by_member(
            system_id, member_id, date_from, date_to
        )

        # then we obtain the percentage of the energy exported
        self.assertEqual(energy_usage_ratio, 6.9494)

    def test__energy_usage_ratio_from_grid_by_member(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # a member id
        member_id = member_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the percentage of used energy from the net of that member
        energy_usage_ratio_from_net = (
            self.monitoring_service.energy_usage_ratio_from_grid_by_member(
                system_id, member_id, date_from, date_to
            )
        )

        # then we obtain the percentage of the energy exported
        self.assertEqual(energy_usage_ratio_from_net, 0.4498)

    def test__energy_usage_ratio_from_selfconsumption_by_member(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # a member id
        member_id = member_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the percentage of selfconsumed energy that member
        energy_production_ratio = (
            self.monitoring_service.energy_usage_ratio_from_selfconsumption_by_member(
                system_id, member_id, date_from, date_to
            )
        )

        # then we obtain the percentage of the energy exported
        self.assertEqual(energy_production_ratio, 0.5502)

    def test__co2save_by_member(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # a member id
        member_id = member_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the CO2 saved by a member
        co2_saved = self.monitoring_service.co2save_by_member(
            system_id, member_id, date_from, date_to
        )

        # then we obtain the number of tones of co2 saved in within that dates
        self.assertEqual(co2_saved, 193777.92)

    def test__daily_generated_energy_by_member(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # a member id
        member_id = member_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the daily generated energy by a member
        daily_generated_energy = self.monitoring_service.daily_production_by_member(
            system_id, member_id, date_from, date_to
        )

        # then we obtain a list of EneryPoints
        self.assertIsInstance(daily_generated_energy, list)
        self.assertGreaterEqual(len(daily_generated_energy), 1)
        for point in daily_generated_energy:
            self.assertIsInstance(point, MeasurePoint)

    def test__generated_energy_by_project(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the generated_energy for that project
        generated_energy = self.monitoring_service.energy_production_by_project(
            system_id, date_from, date_to
        )

        # then we obtain the value of the total generated energy between that dates of that project
        self.assertEqual(generated_energy, 1993.6)

    def test__selfconsumed_energy_by_project(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the selfconsumed_energy of a project
        selfconsumed_energy = self.monitoring_service.energy_selfconsumption_by_project(
            system_id, date_from, date_to
        )

        # then we obtain the value of the selfconsumed energy between that dates of that project
        self.assertEqual(selfconsumed_energy, 161.481)

    def test__exported_energy_by_project(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the exported_energy of a project
        exported_energy = self.monitoring_service.energy_gridinjection_by_project(
            system_id, date_from, date_to
        )

        # then we obtain the value of the exported energy between that dates of that project
        self.assertEqual(exported_energy, 1832.119)

    def test__relation_exported_energy_and_selfconsumed_energy(self):
        # given two dates
        date_from = date(2024, 4, 1)
        date_to = date(2024, 4, 30)
        # a valid system id
        system_id = project_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the exported_energy for that project
        exported_energy = self.monitoring_service.energy_gridinjection_by_project(
            system_id, date_from, date_to
        )
        # and we ask for the selfconsumed_energy for the same project
        selfconsumed_energy = self.monitoring_service.energy_selfconsumption_by_project(
            system_id, date_from, date_to
        )

        # then the sum of these two values must be the total generated_energy
        generated_energy = self.monitoring_service.energy_production_by_project(
            system_id, date_from, date_to
        )

        self.assertEqual(exported_energy + selfconsumed_energy, generated_energy)

    def test__energy_selfconsumption_ratio_by_project(self):
        # given two dates
        date_from = date(2025, 3, 1)
        date_to = date(2025, 3, 31)
        # a valid system id
        system_id = project_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for percentage of energy self-consumed
        selfconsumed_ratio = self.monitoring_service.energy_selfconsumption_ratio(
            system_id, date_from, date_to
        )

        # then we obtain the value of the generated energy between that dates
        self.assertEqual(selfconsumed_ratio, 0.1042)

    def test__energy_surplus_ratio_by_project(self):
        # given two dates
        date_from = date(2025, 3, 1)
        date_to = date(2025, 3, 31)
        # a valid system id
        system_id = project_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for percentage of surplus energy
        surplus_ratio = self.monitoring_service.energy_surplus_ratio(
            system_id, date_from, date_to
        )

        # then we obtain the value of the surplus energy between that dates
        self.assertEqual(surplus_ratio, 0.8958)

    def test__energy_usage_ratio_from_grid_by_project(self):
        # given two dates
        date_from = date(2025, 3, 1)
        date_to = date(2025, 3, 31)
        # a valid system id
        system_id = project_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the energy usage ratio from the grid
        energy_usage_ratio = self.monitoring_service.energy_usage_ratio_from_grid(
            system_id, date_from, date_to
        )

        # then we obtain the value of the ratio of the energy from
        # the grid between that dates
        self.assertEqual(energy_usage_ratio, 0.5985)

    def test__energy_usage_ratio_from_selfconsumption_by_project(self):
        # given two dates
        date_from = date(2025, 3, 1)
        date_to = date(2025, 3, 31)
        # a valid system id
        system_id = project_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the energy usage ratio from selfconsumption
        energy_usage_ratio = (
            self.monitoring_service.energy_usage_ratio_from_selfconsumption(
                system_id, date_from, date_to
            )
        )

        # then we obtain the value of the ratio of the energy from
        # the grid between that dates
        self.assertEqual(energy_usage_ratio, 0.4015)

    def test__relation_energy_usage_by_project(self):
        # given two dates
        date_from = date(2025, 3, 1)
        date_to = date(2025, 3, 31)
        # a valid system id
        system_id = project_code
        # and a monitoring service
        # self.monitoring_service

        # when we ask for the energy usage ratio from selfconsumption
        energy_usage_ratio_from_selfconsumption = (
            self.monitoring_service.energy_usage_ratio_from_selfconsumption(
                system_id, date_from, date_to
            )
        )
        # and we ask for the energy usage ratio from the grid
        energy_usage_ratio_from_grid = (
            self.monitoring_service.energy_usage_ratio_from_grid(
                system_id, date_from, date_to
            )
        )

        # if we sum both values
        energy_usage = (
            energy_usage_ratio_from_selfconsumption + energy_usage_ratio_from_grid
        )
        # that value must be 1
        self.assertEqual(energy_usage, 1)
