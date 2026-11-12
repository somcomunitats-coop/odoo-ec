from unittest.mock import patch

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.energy_communities.config import PLATFORM_ADMIN

from ..wizards.selfconsumption_import_wizard import (
    HIDDEN_INSCRIPTION_FORM_FIELDS,
    INSCRIPTION_IMPORT_DELIMITER,
    SAMPLE_COUNT_MAX,
)


@tagged("-at_install", "post_install", "energy_selfconsumption")
class TestInscriptionImportWizard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.project = self.env["energy_selfconsumption.selfconsumption"].create(
            {
                "name": "Sample import project",
                "type": self.env.ref(
                    "energy_selfconsumption.selfconsumption_project_type"
                ).id,
                "street": "Carrer de Sants 1",
                "zip": "08014",
                "city": "Barcelona",
                "state_id": self.env.ref("base.state_es_b").id,
                "country_id": self.env.ref("base.es").id,
                "owner_id": self.company.partner_id.id,
                "power": 10,
            }
        )
        self.wizard = (
            self.env["energy_selfconsumption.selfconsumption_import.wizard"]
            .with_context(active_id=self.project.id)
            .create({"sample_count": 2})
        )

    def _as_platform_admin(self):
        return patch.object(
            type(self.env.user), "get_current_role", return_value=PLATFORM_ADMIN
        )

    def _sample_partners(self):
        return (
            self.env["res.partner"]
            .sudo()
            .search([("ref", "=like", "sample-inscription-%")])
        )

    def test_delimiter_defaults_to_semicolon(self):
        self.assertEqual(self.wizard.delimiter, INSCRIPTION_IMPORT_DELIMITER)

    def test_hidden_fields_alert_lists_only_disabled_flags(self):
        self.project.write(
            {
                "conf_show_contracted_power": False,
                "conf_show_access_tariff": True,
                "conf_used_in_selfconsumption": False,
                "conf_vulnerability_situation": False,
                "conf_bank_details": False,
                "conf_cadastral_reference_readonly": False,
                "conf_show_annual_consumption": False,
                "conf_show_participation": True,
            }
        )
        self.wizard.invalidate_recordset(["hidden_fields_alert"])
        alert = str(self.wizard.hidden_fields_alert)
        labels = self.wizard._hidden_form_field_labels(self.project)
        self.assertIn("No ", alert)
        self.assertTrue(labels)
        for label in labels:
            self.assertIn(label, alert)
        shown = self.project.fields_get(["conf_show_access_tariff"])[
            "conf_show_access_tariff"
        ]["string"]
        self.assertNotIn(f"No {shown}", alert)
        self.assertLess(len(labels), len(HIDDEN_INSCRIPTION_FORM_FIELDS))

    def test_template_download_uses_the_shipped_file_until_settings_change(self):
        attachment = self.env[
            "res.config.settings"
        ]._inscription_import_template_attachment()
        self.assertEqual(
            attachment,
            self.env.ref(
                "energy_selfconsumption.selfconsumption_table_example_attachment"
            ),
        )
        action = self.wizard.download_template_button()
        self.assertIn(str(attachment.id), action["url"])

    def test_settings_keep_an_uploaded_template(self):
        settings = self.env["res.config.settings"].create(
            {
                "inscription_import_template": "YQ==",
                "inscription_import_template_filename": "custom_template.csv",
            }
        )
        settings._save_inscription_import_template()
        attachment = self.env[
            "res.config.settings"
        ]._inscription_import_template_attachment()
        self.assertEqual(attachment.name, "custom_template.csv")
        self.assertNotEqual(
            attachment,
            self.env.ref(
                "energy_selfconsumption.selfconsumption_table_example_attachment"
            ),
        )

    def test_generate_is_idempotent_and_delete_removes_the_batch(self):
        with self._as_platform_admin():
            self.wizard.action_generate_sample_inscriptions()
            first = self._sample_partners()
            self.assertEqual(len(first), 2)
            self.assertEqual(
                set(first.mapped("name")),
                {"Sample Inscription 0001", "Sample Inscription 0002"},
            )
            inscriptions = self.env[
                "energy_selfconsumption.inscription_selfconsumption"
            ].search([("partner_id", "in", first.ids)])
            self.assertEqual(len(inscriptions), 2)
            self.assertEqual(
                set(inscriptions.mapped("selfconsumption_project_id").ids),
                {self.project.id},
            )
            cups = inscriptions.mapped("supply_point_id.code")
            self.assertEqual(len(set(cups)), 2)

            self.wizard.action_generate_sample_inscriptions()
            self.assertEqual(len(self._sample_partners()), 2)

            self.wizard.sample_count = 3
            self.wizard.action_generate_sample_inscriptions()
            self.assertEqual(len(self._sample_partners()), 3)

            self.wizard.action_delete_sample_inscriptions()
            self.assertFalse(self._sample_partners())
            self.assertFalse(
                self.env["energy_selfconsumption.inscription_selfconsumption"].search(
                    [("selfconsumption_project_id", "=", self.project.id)]
                )
            )

    def test_sample_actions_require_platform_admin(self):
        with patch.object(
            type(self.env.user), "get_current_role", return_value="role_ce_manager"
        ):
            with self.assertRaises(AccessError):
                self.wizard.action_generate_sample_inscriptions()
            with self.assertRaises(AccessError):
                self.wizard.action_delete_sample_inscriptions()
        self.assertFalse(self._sample_partners())

    def test_sample_count_cannot_exceed_the_maximum(self):
        with self.assertRaises(ValidationError):
            self.wizard.sample_count = SAMPLE_COUNT_MAX + 1
