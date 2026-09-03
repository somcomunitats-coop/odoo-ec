from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_selfconsumption.config import (
    DISTRIBUTION_STATE_ACTIVE,
    DISTRIBUTION_STATE_CANCELLED,
)


@tagged("-at_install", "post_install", "energy_selfconsumption")
class TestDistributionTableReplacement(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selfconsumption = cls.env.ref(
            "energy_selfconsumption.selfconsumption_1_community_1_demo"
        )

    def _create_tables_for_period(self, start, end, change_date):
        cancelled = self.env["energy_selfconsumption.distribution_table"].create(
            {
                "selfconsumption_project_id": self.selfconsumption.id,
                "type": "fixed",
                "state": DISTRIBUTION_STATE_CANCELLED,
                "date_start": start,
                "date_end": change_date - timedelta(days=1),
            }
        )
        active = self.env["energy_selfconsumption.distribution_table"].create(
            {
                "selfconsumption_project_id": self.selfconsumption.id,
                "type": "fixed",
                "state": DISTRIBUTION_STATE_ACTIVE,
                "date_start": change_date,
            }
        )
        return active, cancelled

    def test_table_change_detected_inside_period(self):
        period_start = date(2026, 7, 1)
        period_end = date(2026, 9, 30)
        change_date = date(2026, 7, 20)
        self._create_tables_for_period(period_start, period_end, change_date)

        active, cancelled = self.selfconsumption.get_table_change_in_period(
            period_start, period_end
        )
        self.assertTrue(active)
        self.assertTrue(cancelled)
        self.assertEqual(active.date_start, change_date)
        self.assertEqual(cancelled.date_end, date(2026, 7, 19))

    def test_table_change_on_first_day_is_still_detected_on_tables(self):
        period_start = date(2026, 7, 1)
        period_end = date(2026, 9, 30)
        self._create_tables_for_period(period_start, period_end, period_start)
        active, cancelled = self.selfconsumption.get_table_change_in_period(
            period_start, period_end
        )
        self.assertTrue(active)
        self.assertTrue(cancelled)
        self.assertEqual(active.date_start, period_start)
        # Invoicing wizard must treat this as a regular full period (not a split)
        self.assertEqual(active.date_start, period_start)

    def test_replacement_wizard_rejects_date_outside_next_period(self):
        contracts = self.selfconsumption.get_active_contracts()
        if not contracts:
            self.skipTest("Demo project has no active contracts")
        period_start = contracts[0].next_period_date_start
        period_end = contracts[0].next_period_date_end
        if not period_start or not period_end:
            self.skipTest("Demo contracts have no invoicing period")
        wizard = self.env[
            "energy_selfconsumption.set_new_distribution_table.wizard"
        ].create(
            {
                "selfconsumption_id": self.selfconsumption.id,
                "execution_date": period_end + timedelta(days=1),
            }
        )
        self.assertTrue(wizard.range_info_notice)
        self.assertTrue(wizard.show_out_of_range_notice)
        self.assertTrue(wizard.out_of_range_notice)
        self.assertIn("text-danger", wizard.out_of_range_notice)
        with self.assertRaises(ValidationError) as error:
            wizard.action_confirm()
        self.assertIn(
            "You cannot run a distribution table replacement outside",
            str(error.exception),
        )

    def test_replacement_wizard_shows_range_info_when_date_is_inside_period(self):
        contracts = self.selfconsumption.get_active_contracts()
        if not contracts:
            self.skipTest("Demo project has no active contracts")
        period_start = contracts[0].next_period_date_start
        period_end = contracts[0].next_period_date_end
        if not period_start or not period_end:
            self.skipTest("Demo contracts have no invoicing period")
        wizard = self.env[
            "energy_selfconsumption.set_new_distribution_table.wizard"
        ].create(
            {
                "selfconsumption_id": self.selfconsumption.id,
                "execution_date": period_start,
            }
        )
        self.assertTrue(wizard.show_range_info_notice)
        self.assertTrue(wizard.range_info_notice)
        self.assertFalse(wizard.show_out_of_range_notice)
        self.assertIn(
            period_start.strftime("%d/%m/%Y"),
            wizard.range_info_notice,
        )
        self.assertIn("<strong>", wizard.range_info_notice)

    def test_advance_invoice_section_note_includes_period_dates(self):
        wizard = self.env[
            "energy_selfconsumption.set_new_distribution_table.wizard"
        ].create(
            {
                "selfconsumption_id": self.selfconsumption.id,
                "execution_date": date(2026, 5, 3),
            }
        )
        note = wizard._get_advance_invoice_section_note(
            period_start=date(2026, 4, 1),
            period_end=date(2026, 5, 2),
        )
        self.assertIn("01/04/2026", note)
        self.assertIn("02/05/2026", note)
        self.assertIn("03/05/2026", note)
        self.assertIn("32", note)
        self.assertNotIn("()", note)

    def test_remaining_period_section_note_includes_period_end(self):
        wizard = self.env["energy_selfconsumption.invoicing.wizard"].create({})
        note = wizard._get_remaining_period_section_note(
            date(2026, 5, 3), period_end=date(2026, 6, 30)
        )
        self.assertIn("03/05/2026", note)
        self.assertIn("30/06/2026", note)
        self.assertIn("59", note)
        self.assertNotIn("()", note)
