from datetime import date
from unittest.mock import patch

from odoo.tests.common import TransactionCase

from ..backends.arkenova_backend import ArkenovaBackend
from ..backends.exceptions import RequestError
from .backends_data import (
    arkenova_data,
    member_code,
    project_code,
    unknown_project_code,
)


class TestArkenovaBackend(TransactionCase):
    def setUp(self):
        self.maxDiff = None
        self.url = arkenova_data["url"]
        self.token = arkenova_data["token"]

        self.endpoint_patch = patch.dict(
            ArkenovaBackend._endpoints,
            {"project_daily_metrics": "project/v1/{system_id}"},
            clear=True,
        )

    def tearDown(self):
        if self.endpoint_patch._original:
            self.endpoint_patch.stop()

    def test__create_backend(self):
        # given some connection data to arkenova
        url = "https://arkenova.foo.url"
        token = "tokennekot5"

        # when we create a new arkenova backend with that credentials
        arkenova = ArkenovaBackend(url, token)

        # then we have an instance of that backend
        self.assertIsInstance(arkenova, ArkenovaBackend)

    def test__project_daily_metrics__ok(self):
        # given a project and an arkenova backend instance
        project_id = project_code
        arkenova = ArkenovaBackend(self.url, self.token)

        # when we ask for the daily metrics between two dates in iso format
        from_date = str(date(2024, 4, 28))
        to_date = str(date(2024, 4, 29))
        daily_metrics = arkenova.project_daily_metrics(project_id, from_date, to_date)

        # then we obtain a list of metrics for the date period especified
        self.assertGreater(len(daily_metrics), 0)
        self.assertListEqual(
            daily_metrics,
            [
                {
                    "energy_consumption": "13.667",
                    "energy_exported": "68.690",
                    "energy_production": "76.040",
                    "selfconsumption": "7.350",
                    "timestamp": "2024-04-28",
                },
                {
                    "energy_consumption": "16.311",
                    "energy_exported": "31.693",
                    "energy_production": "36.400",
                    "selfconsumption": "4.707",
                    "timestamp": "2024-04-29",
                },
            ],
        )

    def test__project_daily_metrics__wrong_from_date(self):
        # given a project and an arkenova backend instance
        project_id = project_code
        arkenova = ArkenovaBackend(self.url, self.token)

        # when we ask for the daily metrics without from_date
        from_date = ""
        to_date = str(date(2024, 4, 28))

        # then an arkenova exception is raised
        with self.assertRaises(RequestError) as excp_manager:
            daily_metrics = arkenova.project_daily_metrics(
                project_id, from_date, to_date
            )

        self.assertEqual(excp_manager.exception.error_code, 400)
        self.assertEqual(
            excp_manager.exception.message, "Invalid from_date parameter format"
        )

    def test__project_daily_metrics__wrong_to_date(self):
        # given a project and an arkenova backend instance
        project_id = project_code
        arkenova = ArkenovaBackend(self.url, self.token)

        # when we ask for the daily metrics without to_date
        from_date = str(date(2024, 4, 28))
        to_date = ""

        # then an arkenova exception is raised
        with self.assertRaises(RequestError) as excp_manager:
            daily_metrics = arkenova.project_daily_metrics(
                project_id, from_date, to_date
            )

        self.assertEqual(excp_manager.exception.error_code, 400)
        self.assertEqual(
            excp_manager.exception.message, "Invalid to_date parameter format"
        )

    def test__project_daily_metrics__wrong_dates(self):
        # given a project and an arkenova backend instance
        project_id = project_code
        arkenova = ArkenovaBackend(self.url, self.token)

        # when we ask for the daily metrics between two incorrect dates
        from_date = str(date(2024, 4, 29))
        to_date = str(date(2024, 4, 27))

        # then an arkenova exception is raised
        with self.assertRaises(RequestError) as excp_manager:
            daily_metrics = arkenova.project_daily_metrics(
                project_id, from_date, to_date
            )

        self.assertEqual(excp_manager.exception.error_code, 400)
        self.assertEqual(excp_manager.exception.message, "Invalid date range")

    def test__project_daily_metrics__wrong_endpoint(self):
        # given project id and an arkenova backend instance with an incorrect endpoint
        project_id = project_code

        arkenova = ArkenovaBackend(self.url, self.token)

        # when we ask for the daily metrics between two correct dates
        from_date = str(date(2024, 4, 27))
        to_date = str(date(2024, 4, 29))

        # then an arkenova exception is raised
        self.endpoint_patch.start()
        with self.assertRaises(RequestError) as excp_manager:
            daily_metrics = arkenova.project_daily_metrics(
                project_id, from_date, to_date
            )

        self.assertEqual(excp_manager.exception.error_code, 400)
        self.assertEqual(excp_manager.exception.message, "Wrong URL format")

    def test__project_daily_metrics__wrong_project_id(self):
        # given project id that has an incorrect format
        project_id = "ES54678"
        arkenova = ArkenovaBackend(self.url, self.token)

        # when we ask for the daily metrics between two correct dates
        from_date = str(date(2024, 4, 27))
        to_date = str(date(2024, 4, 29))

        # then an arkenova exception is raised
        with self.assertRaises(RequestError) as excp_manager:
            daily_metrics = arkenova.project_daily_metrics(
                project_id, from_date, to_date
            )

        self.assertEqual(excp_manager.exception.error_code, 400)
        self.assertEqual(excp_manager.exception.message, "Invalid CAU format")

    def test__project_daily_metrics__unknown_project_id(self):
        # given project id that is not under akernova systems
        project_id = unknown_project_code

        arkenova = ArkenovaBackend(self.url, self.token)

        # when we ask for the daily metrics between two correct dates
        from_date = str(date(2024, 4, 27))
        to_date = str(date(2024, 4, 29))

        # then an arkenova exception is raised
        with self.assertRaises(RequestError) as excp_manager:
            daily_metrics = arkenova.project_daily_metrics(
                project_id, from_date, to_date
            )
        self.assertEqual(excp_manager.exception.error_code, 404)
        self.assertEqual(excp_manager.exception.message, "Unable to find requested CAU")

    def test__project_daily_metrics_by_member__ok(self):
        # given a project and an arkenova backend instance
        project_id = project_code
        member_id = member_code
        arkenova = ArkenovaBackend(self.url, self.token)

        # when we ask for the daily metrics between two dates in iso format
        from_date = str(date(2024, 4, 28))
        to_date = str(date(2024, 4, 29))
        daily_metrics = arkenova.project_daily_metrics_by_member(
            project_id, member_id, from_date, to_date
        )

        # then we obtain a list of metrics for the date period especified
        self.assertGreater(len(daily_metrics), 0)
        self.assertListEqual(
            daily_metrics,
            [
                {
                    "energy_consumption": "7.484",
                    "energy_exported": "40.496",
                    "energy_production": "45.624",
                    "selfconsumption": "5.128",
                    "timestamp": "2024-04-28",
                },
                {
                    "energy_consumption": "4.651",
                    "energy_exported": "19.844",
                    "energy_production": "21.840",
                    "selfconsumption": "1.996",
                    "timestamp": "2024-04-29",
                },
            ],
        )
