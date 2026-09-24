from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

INVALID_CUPS = "ES0021830910216004BC"
VALID_CUPS = "ES0396269610283393CF"


@tagged("-at_install", "post_install", "energy_selfconsumption")
class TestCreateInscriptionCups(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.company.partner_id.write(
            {
                "country_id": self.env.ref("base.es").id,
                "state_id": self.env.ref("base.state_es_b").id,
            }
        )
        self.partner = self.env["res.partner"].create(
            {
                "name": "Inscription CUPS partner",
                "vat": "ESA00000000",
                "company_id": self.company.id,
            }
        )
        self.service = self.env[
            "energy_selfconsumption.create_inscription_selfconsumption"
        ]
        self.project = self.env["energy_selfconsumption.selfconsumption"].search(
            [("company_id", "=", self.company.id)], limit=1
        )

    def _values(self, cups):
        return {
            "inscription_partner_id_vat": self.partner.vat,
            "supplypoint_owner_id_vat": self.partner.vat,
            "supplypoint_cups": cups,
            "supplypoint_street": "Test street",
            "supplypoint_city": "Barcelona",
            "supplypoint_zip": "08014",
            "supplypoint_cadastral_reference": "",
            "supplypoint_contracted_power": "3.0",
        }

    def _supply_points(self, cups):
        return (
            self.env["energy_selfconsumption.supply_point"]
            .sudo()
            .search([("code", "=", cups)])
        )

    def test_invalid_cups_is_rejected_and_creates_nothing(self):
        Inscription = self.env["energy_project.inscription"].sudo()
        before_inscriptions = Inscription.search_count([])
        service_model = type(self.service)
        with patch.object(
            service_model, "_get_partner", return_value=self.partner
        ), patch.object(service_model, "_is_cooperator", return_value=True):
            error, message = self.service.create_inscription(
                self._values(INVALID_CUPS), self.project
            )

        self.assertTrue(error)
        self.assertIn(INVALID_CUPS, str(message))
        self.assertFalse(self._supply_points(INVALID_CUPS))
        self.assertEqual(Inscription.search_count([]), before_inscriptions)

    def test_failure_after_supply_point_create_rolls_back(self):
        if not self.project:
            self.skipTest("No self-consumption project in this company")
        Inscription = self.env["energy_project.inscription"].sudo()
        before_inscriptions = Inscription.search_count([])
        service_model = type(self.service)
        with patch.object(
            service_model, "_get_partner", return_value=self.partner
        ), patch.object(
            service_model, "_is_cooperator", return_value=True
        ), patch.object(
            service_model, "_is_partner_already_registered", return_value=False
        ), patch.object(
            service_model, "_get_participation", return_value=False
        ):
            error, message = self.service.create_inscription(
                self._values(VALID_CUPS), self.project
            )

        self.assertTrue(error)
        self.assertFalse(self._supply_points(VALID_CUPS))
        self.assertEqual(Inscription.search_count([]), before_inscriptions)
