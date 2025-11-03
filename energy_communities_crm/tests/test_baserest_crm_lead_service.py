import json

import requests

import odoo
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.base_rest.tests.common import BaseRestCase

from .testing_cases import _CE_CREATION_API_PAYLOAD

HOST = "localhost"
PORT = odoo.tools.config["http_port"]


class TestBaseRestCRMLeadServiceRestCase(BaseRestCase):
    def setUp(self):
        super().setUp()
        self.auth_api_key = self.env.ref("energy_communities.apikey_web_demo")
        self.session = requests.Session()

    @tagged("endpoints")
    def test_ce_creation_lead_ok(self):
        url = "/api/crm/crm-lead"
        # when we make an api call for creating a crm lead
        response = self.http_post(url, data=_CE_CREATION_API_PAYLOAD)
        # the call is successful
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode("utf-8"))
        self.assertIn("id", content)
        lead_id = content["id"]
        crm_lead = self.env["crm.lead"].browse(lead_id)
        # a crm lead is created
        self.assertTrue(bool(crm_lead))
        # with correct data
        self.assertEqual(
            crm_lead.source_id,
            self.env.ref(
                "energy_communities.{}".format(
                    list(
                        filter(
                            lambda meta: meta["key"] == "source_xml_id",
                            _CE_CREATION_API_PAYLOAD["metadata"],
                        )
                    )[0]["value"]
                )
            ),
        )
        self.assertEqual(
            crm_lead.name,
            "[Alta CE] {lead_id} {lead_name}".format(
                lead_id=lead_id,
                lead_name="TEST CE CREATION name",
            ),
        )
        self.assertEqual(crm_lead.email_from, _CE_CREATION_API_PAYLOAD["email_from"])
        expected_lang = self.env["res.lang"].search(
            [
                (
                    "code",
                    "=",
                    list(
                        filter(
                            lambda meta: meta["key"] == "ce_current_lang",
                            _CE_CREATION_API_PAYLOAD["metadata"],
                        )
                    )[0]["value"],
                )
            ],
            limit=1,
        )
        self.assertEqual(crm_lead.lang_id, expected_lang)
        self.assertEqual(
            crm_lead.street,
            list(
                filter(
                    lambda meta: meta["key"] == "ce_address",
                    _CE_CREATION_API_PAYLOAD["metadata"],
                )
            )[0]["value"],
        )
        self.assertEqual(
            crm_lead.city,
            list(
                filter(
                    lambda meta: meta["key"] == "ce_city",
                    _CE_CREATION_API_PAYLOAD["metadata"],
                )
            )[0]["value"],
        )
        self.assertEqual(
            crm_lead.zip,
            list(
                filter(
                    lambda meta: meta["key"] == "ce_zip",
                    _CE_CREATION_API_PAYLOAD["metadata"],
                )
            )[0]["value"],
        )
        for meta in _CE_CREATION_API_PAYLOAD["metadata"]:
            meta_line = crm_lead.metadata_line_ids.filtered(
                lambda line: line.key == meta["key"]
            )
            self.assertTrue(meta_line)
            self.assertEqual(meta_line.value, meta["value"])

    def _add_call_headers(self, headers):
        key_dict = {"API-KEY": self.auth_api_key.key, "accept-language": "es_ES"}
        if headers:
            headers.update(key_dict)
        else:
            headers = key_dict
        return headers

    def http_post(self, url, data, headers=None):
        headers = self._add_call_headers(headers)
        if url.startswith("/"):
            url = "http://{}:{}{}".format(HOST, PORT, url)
            return self.session.post(url, json=data, headers=headers)
