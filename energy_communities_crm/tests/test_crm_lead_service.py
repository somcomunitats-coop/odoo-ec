import json
from functools import partial

import requests

import odoo
from odoo.tests.common import HttpCase, tagged

from odoo.addons.base_rest.tests.common import RegistryMixin

from .testing_cases import _CE_CREATION_API_PAYLOAD

HOST = "localhost"
PORT = odoo.tools.config["http_port"]


@tagged("-at_install", "post_install")
class TestCRMLeadServiceRestCase(HttpCase, RegistryMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpRegistry()

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.timeout = 600
        self.auth_api_key = self.env.ref("energy_communities.apikey_web_demo")
        self.headers = {
            "Content-Type": "application/json",
            "API-KEY": self.auth_api_key.key,
        }
        self.client = partial(self.url_open, headers=self.headers, timeout=self.timeout)
        self.BASE_METADATA_FIXTURE = [
            {"key": "entry_id", "value": "153"},
            {"key": "source_xml_id", "value": "ce_source_creation_ce_proposal"},
            {"key": "current_lang", "value": "ca_ES"},
            {"key": "map_place_ref", "value": "ce-el-bruc"},
            {"key": "company_id", "value": "1"},
            {"key": "ce_name", "value": "Test final connectat"},
            {"key": "ce_description", "value": "test"},
            {"key": "ce_address", "value": "Cami Ral 190"},
            {"key": "ce_city", "value": "Mataró"},
            {"key": "ce_state", "value": "Barcelona"},
            {"key": "ce_zip", "value": "08301"},
            {
                "key": "ce_map_place_creation_preference",
                "value": "Vincular la teva comunitat amb el punt del MAPA existent.",
            },
            {
                "key": "ce_services",
                "value": "ce_tag_energy_efficiency,ce_tag_sustainable_mobility",
            },
            {"key": "ce_number_of_members", "value": "12"},
            {"key": "ce_creation_date", "value": "2023-07-20"},
            {"key": "ce_vat", "value": "38868016G"},
            {"key": "contact_person_name", "value": "dani"},
            {"key": "contact_person_surname", "value": "Quilez"},
            {"key": "email_from", "value": "dani.quilez@gmail.com"},
            {"key": "contact_phone", "value": "654842056"},
            {"key": "contact2_firstname", "value": "dani2"},
            {"key": "contact2_surname", "value": "quilez2"},
            {"key": "contact2_email", "value": "dani.palomar@coopdevs.org"},
            {"key": "contact2_phone", "value": "1234567"},
            {"key": "comments", "value": "test demo"},
        ]
        self.GOOD_METADATA_FIXTURE = [
            {"key": "coordinator_landing_id", "value": "1234"},
            {"key": "known_coordinator", "value": "yes"},
            {"key": "coordinator_name", "value": "PRUEBA DE QUE EXISTE"},
        ]

        self.NO_COORDINATOR_METADATA_FIXTURE = [
            {"key": "coordinator_landing_id", "value": "abc"},
            {"key": "known_coordinator", "value": "yes"},
            {"key": "coordinator_name", "value": "PRUEBA DE QUE NO EXISTE"},
        ]

        self.NO_COORDINATOR_KNOW_METADATA_FIXTURE = [
            {"key": "coordinator_landing_id", "value": "abc"},
            {"key": "known_coordinator", "value": "no"},
            {"key": "coordinator_name", "value": "PRUEBA DE QUE NO EXISTE"},
        ]

    def test_create_crm_lead__ok(self):
        # given http_client
        # self.url_open
        # and a valid data
        data = {
            "name": "ce_source_creation_ce_proposal FULL",
            "email_from": "dani@daniquilez.com",
            "company_id": 1,
            "metadata": self.BASE_METADATA_FIXTURE + self.GOOD_METADATA_FIXTURE,
        }

        # when we call for the creation of the crm lead
        response = self.client("/api/crm/crm-lead/create", data=json.dumps(data))
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and a correct content
        content = response.json()
        self.assertEqual(content["message"], "Creation ok")
        self.assertTrue("id" in content)
        # and a crm_lead exists
        crm_lead = self.env["crm.lead"].browse(content["id"])
        self.assertTrue(crm_lead.exists())
        # and the coordinator_id is in the metadata
        coordinator_id = crm_lead.metadata_line_ids.filtered(
            lambda meta: meta.key == "coordinator_id"
        ).value
        self.assertTrue(coordinator_id)

    def test_create_crm_lead__no_coordinator(self):
        # given http_client
        # self.url_open
        # and a valid data
        data = {
            "name": "ce_source_creation_ce_proposal FULL",
            "email_from": "dani@daniquilez.com",
            "company_id": 1,
            "metadata": self.BASE_METADATA_FIXTURE
            + self.NO_COORDINATOR_METADATA_FIXTURE,
        }

        # when we call for the creation of the crm lead
        response = self.client("/api/crm/crm-lead/create", data=json.dumps(data))
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and a correct content
        content = response.json()
        self.assertEqual(content["message"], "Creation ok")
        self.assertTrue("id" in content)
        # and a crm_lead exists
        crm_lead = self.env["crm.lead"].browse(content["id"])
        self.assertTrue(crm_lead.exists())
        # and the coordinator_id is not in the metadata
        coordinator_id = crm_lead.metadata_line_ids.filtered(
            lambda meta: meta.key == "coordinator_id"
        ).value
        self.assertFalse(coordinator_id)

    def test_create_crm_lead__no_coordinator_know(self):
        # given http_client
        # self.url_open
        # and a valid data
        data = {
            "name": "ce_source_creation_ce_proposal FULL",
            "email_from": "dani@daniquilez.com",
            "company_id": 1,
            "metadata": self.BASE_METADATA_FIXTURE
            + self.NO_COORDINATOR_KNOW_METADATA_FIXTURE,
        }
        # when we call for the creation of the crm lead
        response = self.client("/api/crm/crm-lead/create", data=json.dumps(data))
        # then we obtain a 200 response code
        self.assertEqual(response.status_code, 200)
        # and a correct content
        content = response.json()
        self.assertEqual(content["message"], "Creation ok")
        self.assertTrue("id" in content)
        # and a crm_lead exists
        crm_lead = self.env["crm.lead"].browse(content["id"])
        self.assertTrue(crm_lead.exists())
        # and the coordinator_id is not in the metadata
        coordinator_id = crm_lead.metadata_line_ids.filtered(
            lambda meta: meta.key == "coordinator_id"
        ).value
        self.assertFalse(coordinator_id)
        known_coordinator = crm_lead.metadata_line_ids.filtered(
            lambda meta: meta.key == "known_coordinator"
        ).value
        self.assertEqual(known_coordinator, "no")

    def test_create_crm_lead__bad_request(self):
        # given http_client
        # self.url_open
        # and non valid data
        data = {
            "name": "ce_source_creation_ce_proposal FULL",
            "email_from": "dani@daniquilez.com",
            "metadata": [],
        }
        # when we call for the creation of the crm lead
        response = self.client("/api/crm/crm-lead/create", data=json.dumps(data))
        # then we obtain a 400 response code. Bad request.
        self.assertEqual(response.status_code, 400)
