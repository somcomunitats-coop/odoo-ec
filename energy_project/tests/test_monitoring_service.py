from odoo.tests.common import TransactionCase

from ..backends import ArkenovaBackend
from ..services import MonitoringService
from .backends_data import arkenova_data


class TestMonitoringService(TransactionCase):
    def setUp(self):
        self.maxDiff = None
        self.backend = ArkenovaBackend(**arkenova_data)

    def test__create_monitoring_service(self):
        # given a backend that provide valid data
        backend = self.backend

        # when we create an instance of a monitoring service with that backend
        monitoring_service = MonitoringService(backend=backend)

        # then we have an instance of that service
        self.assertIsInstance(monitoring_service, MonitoringService)
