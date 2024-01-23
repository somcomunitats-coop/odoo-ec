from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import common
from odoo.tools import mute_logger


class TestServiceContract(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.service_1 = self.env["energy_project.service"].create(
            {"name": "Service 1"}
        )
        self.service_2 = self.env["energy_project.service"].create(
            {"name": "Service 2"}
        )
        self.service_3 = self.env["energy_project.service"].create(
            {"name": "Service 3"}
        )
        self.provider_1 = self.env["energy_project.provider"].create(
            {
                "name": "Provider 1",
                "service_available_ids": [
                    (0, 0, {"service_id": self.service_1.id}),
                    (0, 0, {"service_id": self.service_2.id}),
                ],
            }
        )
        self.provider_2 = self.env["energy_project.provider"].create(
            {
                "name": "Provider 2",
                "service_available_ids": [(0, 0, {"service_id": self.service_2.id})],
            }
        )
        self.provider_3 = self.env["energy_project.provider"].create(
            {
                "name": "Provider 3",
                "service_available_ids": [
                    (0, 0, {"service_id": self.service_1.id}),
                    (0, 0, {"service_id": self.service_2.id}),
                    (0, 0, {"service_id": self.service_3.id}),
                ],
            }
        )
        self.project_type = self.env["energy_project.project_type"].create(
            {"name": "Project Type"}
        )
        self.project = self.env["energy_project.project"].create(
            {
                "name": "Project 1",
                "type": self.project_type.id,
                "state": "draft",
                "street": "Carrer de Sants, 79",
                "zip": "08014",
                "city": "Barcelona",
                "state_id": self.env.ref("base.state_es_b").id,
                "country_id": self.env.ref("base.es").id,
            }
        )

    @mute_logger("odoo.sql_db")
    def test_unique(self):
        self.project.write(
            {
                "service_contract_ids": [
                    (
                        0,
                        0,
                        {
                            "service_id": self.service_1.id,
                            "provider_id": self.provider_1.id,
                        },
                    )
                ]
            }
        )

        with self.assertRaises(IntegrityError):
            self.project.write(
                {
                    "service_contract_ids": [
                        (
                            0,
                            0,
                            {
                                "service_id": self.service_1.id,
                                "provider_id": self.provider_1.id,
                            },
                        )
                    ]
                }
            )

    def test_check_provider_id(self):
        self.assertTrue(
            self.project.write(
                {
                    "service_contract_ids": [
                        (
                            0,
                            0,
                            {
                                "service_id": self.service_1.id,
                                "provider_id": self.provider_1.id,
                            },
                        )
                    ]
                }
            )
        )
        with self.assertRaises(ValidationError):
            self.project.write(
                {
                    "service_contract_ids": [
                        (
                            0,
                            0,
                            {
                                "service_id": self.service_1.id,
                                "provider_id": self.provider_2.id,
                            },
                        )
                    ]
                }
            )

    def test_compute_available_providers_ids(self):
        self.service_contract_1 = self.env["energy_project.service_contract"].create(
            {
                "service_id": self.service_3.id,
                "provider_id": self.provider_3.id,
                "project_id": self.project.id,
                "active": True,
            }
        )
        expected_available_providers_ids_1 = [self.provider_3.id]
        self.assertEqual(
            self.service_contract_1.available_providers_ids.ids,
            expected_available_providers_ids_1,
        )

        self.service_contract_2 = self.env["energy_project.service_contract"].create(
            {
                "service_id": self.service_2.id,
                "provider_id": self.provider_2.id,
                "project_id": self.project.id,
                "active": True,
            }
        )
        expected_available_providers_ids_2 = [
            self.provider_1.id,
            self.provider_2.id,
            self.provider_3.id,
        ]
        self.assertEqual(
            self.service_contract_2.available_providers_ids.ids,
            expected_available_providers_ids_2,
        )
