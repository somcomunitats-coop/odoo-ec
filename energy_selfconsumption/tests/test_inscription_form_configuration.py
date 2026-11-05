from types import SimpleNamespace

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


def _project(**overrides):
    values = {
        "conf_show_contracted_power": True,
        "conf_show_access_tariff": True,
        "conf_show_annual_consumption": True,
        "conf_show_participation": True,
        "conf_bank_details": True,
        "conf_accept_pending_subscription": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@tagged("-at_install", "post_install", "energy_selfconsumption")
class TestInscriptionFormConfiguration(TransactionCase):
    def setUp(self):
        super().setUp()
        self.service = self.env[
            "energy_selfconsumption.create_inscription_selfconsumption"
        ]
        self.company = self.env.company
        self.partner = self.env["res.partner"].create(
            {
                "name": "Form configuration partner",
                "vat": "ES00000000T",
                "company_id": self.company.id,
                "company_ids": [(4, self.company.id)],
            }
        )
        self.project = self.env["energy_selfconsumption.selfconsumption"].search(
            [("company_id", "=", self.company.id)], limit=1
        )

    def test_vat_search_ignores_letter_case(self):
        found = self.service._get_partner("es00000000t", self.company.id)
        self.assertEqual(found, self.partner)

    def test_tariff_code_ignores_spaces_and_case(self):
        self.assertEqual(self.service.normalize_tariff_code("6.1 TD"), "6.1TD")
        self.assertEqual(self.service.normalize_tariff_code("3.0tdve"), "3.0TDVE")
        self.assertFalse(self.service.normalize_tariff_code("9.9TD"))

    def test_power_and_tariff_must_match_existing_rules(self):
        self.assertTrue(self.service.tariff_matches_power("2.0TD", 10))
        self.assertFalse(self.service.tariff_matches_power("3.0TD", 10))
        self.assertTrue(self.service.tariff_matches_power("3.0TDVE", 10))
        self.assertTrue(self.service.tariff_matches_power("6.1TD", 10))

    def test_hidden_fields_are_ignored_and_tariff_comes_from_power(self):
        values = {
            "inscription_partner_id_vat": "es00000000t",
            "supplypoint_contracted_power": "20",
            "tariff": "6.2TDVE",
            "inscriptionselfconsumption_annual_electricity_use": "4000",
            "inscriptionselfconsumption_participation": "2",
            "inscription_acc_number": "ES00",
        }
        error = self.service.prepare_inscription_values(
            values,
            _project(
                conf_show_access_tariff=False,
                conf_show_annual_consumption=False,
                conf_show_participation=False,
                conf_bank_details=False,
            ),
        )
        self.assertFalse(error)
        self.assertEqual(values["inscription_partner_id_vat"], "ES00000000T")
        self.assertEqual(values["tariff"], "3.0TD")
        self.assertEqual(values["supplypoint_contracted_power"], 20.0)
        self.assertEqual(
            values["inscriptionselfconsumption_annual_electricity_use"], 0.0
        )
        self.assertNotIn("inscriptionselfconsumption_participation", values)
        self.assertNotIn("inscription_acc_number", values)

    def test_tariff_only_stores_zero_power(self):
        values = {
            "supplypoint_contracted_power": "20",
            "supplypoint_tariff": "6.1 TD",
            "inscriptionselfconsumption_annual_electricity_use": "1000",
            "inscriptionselfconsumption_participation": "1",
        }
        error = self.service.prepare_inscription_values(
            values,
            _project(conf_show_contracted_power=False),
        )
        self.assertFalse(error)
        self.assertEqual(values["tariff"], "6.1TD")
        self.assertEqual(values["supplypoint_contracted_power"], 0.0)

    def test_incompatible_power_is_rejected(self):
        values = {
            "supplypoint_contracted_power": "10",
            "supplypoint_tariff": "3.0TD",
            "inscriptionselfconsumption_annual_electricity_use": "1000",
            "inscriptionselfconsumption_participation": "1",
        }
        error = self.service.prepare_inscription_values(values, _project())
        self.assertIn("incompatible", error)

    def test_blank_visible_tariff_is_required(self):
        values = {
            "supplypoint_contracted_power": "10",
            "tariff": False,
            "inscriptionselfconsumption_annual_electricity_use": "1000",
            "inscriptionselfconsumption_participation": "1",
        }
        error = self.service.prepare_inscription_values(values, _project())
        self.assertIn("Access tariff is required", error)

    def test_both_supply_fields_hidden_is_rejected(self):
        if not self.project:
            self.skipTest("No self-consumption project in this company")
        with self.assertRaises(ValidationError):
            self.project.write(
                {
                    "conf_show_contracted_power": False,
                    "conf_show_access_tariff": False,
                }
            )

    def test_hidden_participation_uses_the_first_option(self):
        if not self.project or not self.project.conf_participation_ids:
            self.skipTest("Project has no participation options")
        first = self.project.conf_participation_ids[:1]
        found = self.service._get_participation({}, self.project)
        self.assertEqual(found, first)
