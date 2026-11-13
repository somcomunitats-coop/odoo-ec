from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWizardChartUpdateTicketBAI(TransactionCase):
    """Test account chart update integration with TicketBAI."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Get or create company
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test Company TicketBAI",
                "country_id": cls.env.ref("base.es").id,
            }
        )

        # Get chart template
        cls.chart_template = cls.env.ref("l10n_es.account_chart_template_common")

        # Install chart of accounts for company
        cls.chart_template.try_loading(company=cls.company)

        # Get VAT exemption key for tests
        cls.vat_exemption_key = cls.env.ref("l10n_es_ticketbai.tbai_vat_exemption_E1")

        # Create a tax template
        cls.tax_template = cls.env["account.tax.template"].create(
            {
                "name": "Test Tax Template",
                "chart_template_id": cls.chart_template.id,
                "amount": 21.0,
                "type_tax_use": "sale",
            }
        )

        # Create a real tax from template
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "Test Tax",
                "amount": 21.0,
                "type_tax_use": "sale",
                "company_id": cls.company.id,
            }
        )

        # Create fiscal position template with TicketBAI exemptions
        cls.fp_template = cls.env["account.fiscal.position.template"].create(
            {
                "name": "Test FP Template with TicketBAI",
                "chart_template_id": cls.chart_template.id,
                "tbai_vat_regime_key": cls.env.ref(
                    "l10n_es_ticketbai.tbai_vat_regime_01"
                ).id,
            }
        )

        # Create TicketBAI tax exemption template
        cls.tbai_exemption_template = cls.env["account.fp.tbai.tax_template"].create(
            {
                "position_id": cls.fp_template.id,
                "tax_id": cls.tax_template.id,
                "tbai_vat_exemption_key": cls.vat_exemption_key.id,
            }
        )

        # Create real fiscal position
        cls.fp = cls.env["account.fiscal.position"].create(
            {
                "name": "Test FP Template with TicketBAI",
                "company_id": cls.company.id,
                "tbai_vat_regime_key": cls.env.ref(
                    "l10n_es_ticketbai.tbai_vat_regime_01"
                ).id,
            }
        )

        # Monkey patch get_taxes_from_templates to emulate template mapping
        def fake_get_taxes_from_templates(company, template):
            if template == cls.tax_template:
                return cls.tax
            return cls.env["account.tax"]

        cls._original_get_taxes_from_templates = type(
            cls.company
        ).get_taxes_from_templates
        type(cls.company).get_taxes_from_templates = fake_get_taxes_from_templates

    @classmethod
    def tearDownClass(cls):
        type(
            cls.company
        ).get_taxes_from_templates = cls._original_get_taxes_from_templates
        super().tearDownClass()

    def test_diff_fields_handles_tbai_exemptions(self):
        """Test that diff_fields correctly converts TicketBAI exemption templates."""
        # Create wizard
        wizard = self.env["wizard.update.charts.accounts"].create(
            {
                "company_id": self.company.id,
                "chart_template_id": self.chart_template.id,
                "lang": "en_US",
            }
        )

        # Get differences between template and real fiscal position
        with patch.object(type(wizard), "find_tax_by_templates", return_value=False):
            diff = wizard.diff_fields(self.fp_template, self.fp)

        # Check that tbai_vat_exemption_ids is in the diff
        self.assertIn("tbai_vat_exemption_ids", diff)

        # Check that the value is properly converted to ORM commands
        exemption_value = diff["tbai_vat_exemption_ids"]
        self.assertTrue(
            isinstance(exemption_value, (list, tuple)),
            "tbai_vat_exemption_ids should be converted to ORM commands",
        )

    def test_diff_fields_no_changes_when_tbai_synced(self):
        """Ensure diff_fields stays silent when TicketBAI lines already match."""
        wizard = self.env["wizard.update.charts.accounts"].create(
            {
                "company_id": self.company.id,
                "chart_template_id": self.chart_template.id,
                "lang": "en_US",
            }
        )
        self.env["account.fp.tbai.tax"].search(
            [("position_id", "=", self.fp.id)]
        ).unlink()
        self.env["account.fp.tbai.tax"].create(
            {
                "position_id": self.fp.id,
                "tax_id": self.tax.id,
                "tbai_vat_exemption_key": self.vat_exemption_key.id,
            }
        )

        with patch.object(
            type(wizard), "find_tax_by_templates", return_value=self.tax.id
        ):
            diff = wizard.diff_fields(self.fp_template, self.fp)

        self.assertNotIn("tbai_vat_exemption_ids", diff)

    def test_update_fiscal_position_with_tbai_exemptions(self):
        """Test that updating fiscal positions with TicketBAI exemptions works."""
        # Create wizard
        wizard = self.env["wizard.update.charts.accounts"].create(
            {
                "company_id": self.company.id,
                "chart_template_id": self.chart_template.id,
                "lang": "en_US",
                "update_fiscal_position": True,
                "update_tax": False,
                "update_account": False,
                "update_account_group": False,
            }
        )

        with patch.object(type(wizard), "find_tax_by_templates", return_value=False):
            # Find fiscal positions to update
            wizard.action_find_records()
            wizard.fiscal_position_ids.filtered(
                lambda line: line.update_fiscal_position_id != self.fp
            ).unlink()

            # Check if our fiscal position was found
            fp_to_update = wizard.fiscal_position_ids.filtered(
                lambda x: x.update_fiscal_position_id == self.fp
            )

            if fp_to_update:
                try:
                    wizard._update_fiscal_positions()
                except ValueError as e:
                    if "account.fp.tbai.tax_template" in str(e):
                        self.fail(
                            "ValueError raised when updating fiscal position with "
                            f"TicketBAI exemptions: {e}"
                        )
                    raise

                self.assertEqual(
                    len(self.fp.tbai_vat_exemption_ids),
                    len(self.fp_template.tbai_vat_exemption_ids),
                    "Number of exemptions should match",
                )
                self.assertTrue(
                    all(
                        exemption._name == "account.fp.tbai.tax"
                        for exemption in self.fp.tbai_vat_exemption_ids
                    ),
                    "Exemptions should be real records, not templates",
                )

    def test_find_fp_tbai_tax_by_templates(self):
        """Test that find_fp_tbai_tax_by_templates method works correctly."""
        # Create wizard
        wizard = self.env["wizard.update.charts.accounts"].create(
            {
                "company_id": self.company.id,
                "chart_template_id": self.chart_template.id,
                "lang": "en_US",
            }
        )

        self.fp.tbai_vat_exemption_ids.unlink()

        # Test the method
        template_exemptions = self.fp_template.tbai_vat_exemption_ids
        real_exemptions = self.fp.tbai_vat_exemption_ids

        with patch.object(type(wizard), "find_tax_by_templates", return_value=False):
            result = wizard.find_fp_tbai_tax_by_templates(
                template_exemptions, real_exemptions
            )

        # Result should be ORM commands
        self.assertTrue(isinstance(result, list), "Result should be a list")

        # Should contain the real exemption or update command
        self.assertGreaterEqual(len(result), 2, "Expected reset plus create commands")
        self.assertEqual(result[0][0], 5, "First command should reset existing records")
        self.assertEqual(result[1][0], 0, "Second command should create a record")
