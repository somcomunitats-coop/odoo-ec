import json

import requests

import odoo
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.base_rest.tests.common import BaseRestCase

HOST = "localhost"
PORT = odoo.tools.config["http_port"]


class TestCRMLeadServiceRestCase(BaseRestCase):
    def setUp(self):
        super().setUp()
        self.api_key_test = self.env.ref("ce.auth_api_key_platform_admin_demo")
        self.AuthApiKey = self.env["auth.api.key"]
        self.session = requests.Session()

    @tagged("endpoints")
    def test_route_right_create(self):
        url = "/api/crm-lead"
        data = {
            "partner_name": "Aida Sanahuja",
            "email_from": "testmail@hotmail.com",
            "phone": "641708221",
            "odoo_company_id": 1,
            "source_id": 1,
        }

        response = self.http_post(url, data=data)
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content.decode("utf-8"))
        self.assertIn("id", content)

        crm_lead = self.env["crm.lead"].browse(content["id"])
        self.assertEqual(crm_lead.partner_name, data["partner_name"])
        self.assertEqual(crm_lead.phone, data["phone"])
        self.assertEqual(crm_lead.email_from, data["email_from"])
        self.assertEqual(crm_lead.company_id.id, data["odoo_company_id"])
        self.assertEqual(crm_lead.source_id.id, data["source_id"])

    def _add_api_key(self, headers):
        key_dict = {"API-KEY": self.api_key_test.key}
        if headers:
            headers.update(key_dict)
        else:
            headers = key_dict
        return headers

    def http_post(self, url, data, headers=None):
        headers = self._add_api_key(headers)
        if url.startswith("/"):
            url = "http://{}:{}{}".format(HOST, PORT, url)
            return self.session.post(url, json=data, headers=headers)
