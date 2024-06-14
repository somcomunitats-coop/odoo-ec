from datetime import date

from odoo.tests.common import TransactionCase

from ..backends import ArkenovaBackend
from ..services import MonitoringService
from .backends_data import arkenova_data, member_code, project_code


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

    def test__generated_energy_by_member(self):
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
        generated_energy = self.monitoring_service.generated_energy_by_member(
            system_id, member_id, date_from, date_to
        )

        # then we obtain the value of the generated energy between that dates
        self.assertEqual(generated_energy, 1425.198)

    def test__selfconsumed_energy_ratio_by_member(self):
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
            self.monitoring_service.selfconsumed_energy_ratio_by_member(
                system_id, member_id, date_from, date_to
            )
        )

        # then we obtain the value of the generated energy between that dates
        self.assertEqual(selfconsumed_ratio, 0.0668)

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
        self.assertEqual(surplus_ratio, 0.9332)

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
            self.monitoring_service.selfconsumed_energy_ratio_by_member(
                system_id, member_id, date_from, date_to
            )
        )

        # then the sum must be 1
        self.assertEqual(surplus_ratio + selfconsumed_ratio, 1.0)

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
        self.assertEqual(co2_saved, 15412.194)
