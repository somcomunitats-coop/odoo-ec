from datetime import date, timedelta
from unittest import SkipTest
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_selfconsumption.config import (
    DISTRIBUTION_STATE_ACTIVE,
    DISTRIBUTION_STATE_CANCELLED,
    INSCRIPTION_STATE_ACTIVE,
    INSCRIPTION_STATE_CANCELLED,
)


@tagged("-at_install", "post_install", "energy_selfconsumption")
class TestDistributionTableReplacement(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selfconsumption = cls.env.ref(
            "energy_selfconsumption.selfconsumption_1_community_1_demo",
            raise_if_not_found=False,
        )
        if not cls.selfconsumption:
            cls.selfconsumption = cls.env[
                "energy_selfconsumption.selfconsumption"
            ].search([], limit=1)
        if not cls.selfconsumption:
            raise SkipTest("No self-consumption project available")

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

    def test_table_change_on_first_day_is_not_a_mid_period_split(self):
        period_start = date(2026, 7, 1)
        period_end = date(2026, 9, 30)
        self._create_tables_for_period(period_start, period_end, period_start)
        active, cancelled = self.selfconsumption.get_table_change_in_period(
            period_start, period_end
        )
        # The cancelled table ends the day before the period, so invoicing
        # must treat this as a regular full period (not a split).
        self.assertFalse(active)
        self.assertFalse(cancelled)

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
        wizard = self.env["energy_selfconsumption.invoicing.wizard"].new(
            {"invoicing_mode": "energy_delivered"}
        )
        note = wizard._get_remaining_period_section_note(
            date(2026, 5, 3), period_end=date(2026, 6, 30)
        )
        self.assertIn("03/05/2026", note)
        self.assertIn("30/06/2026", note)
        self.assertIn("59", note)
        self.assertNotIn("()", note)

    def _stub_contract(self, **vals):
        defaults = {
            "recurring_invoicing_type": "post-paid",
            "recurring_invoicing_offset": 1,
            "last_date_invoiced": date(2026, 3, 31),
            "next_period_date_start": date(2026, 4, 1),
            "next_period_date_end": date(2026, 6, 30),
            "recurring_next_date": date(2026, 7, 1),
        }
        defaults.update(vals)
        return self.env["contract.contract"].new(defaults)

    def test_expected_recurring_next_date_postpaid_includes_offset(self):
        contract = self._stub_contract()
        self.assertEqual(
            self.selfconsumption._expected_recurring_next_date(contract),
            date(2026, 7, 1),
        )

    def test_expected_recurring_next_date_prepaid_includes_offset(self):
        contract = self._stub_contract(
            recurring_invoicing_type="pre-paid",
            recurring_invoicing_offset=0,
            last_date_invoiced=date(2026, 6, 30),
            next_period_date_start=date(2026, 7, 1),
            next_period_date_end=date(2026, 9, 30),
            recurring_next_date=date(2026, 7, 1),
        )
        self.assertEqual(
            self.selfconsumption._expected_recurring_next_date(contract),
            date(2026, 7, 1),
        )

    def test_check_dates_contract_accepts_postpaid_invoice_offset(self):
        """Obanos-like profile: next invoice is period end + 1 day."""
        contracts = self._stub_contract() | self._stub_contract()
        self.selfconsumption.check_dates_contract(contracts)

    def test_check_dates_contract_rejects_wrong_postpaid_invoice_date(self):
        contract = self._stub_contract(
            recurring_invoicing_offset=0,
            recurring_next_date=date(2026, 7, 1),
        )
        with self.assertRaises(ValidationError) as error:
            self.selfconsumption.check_dates_contract(contract)
        self.assertIn("invoicing offset", str(error.exception))

    def test_align_new_prepaid_alta_joins_project_calendar(self):
        """Replacement date is table validity, not a new invoicing period."""
        contract = self.env["contract.contract"].new(
            {
                "recurring_invoicing_type": "pre-paid",
                "date_start": date(2026, 6, 25),
            }
        )
        with patch.object(
            type(self.selfconsumption), "_write_invoicing_dates_on_contract"
        ) as mocked:
            self.selfconsumption._align_new_contract_period_end(
                contract,
                period_recurring_next_date=date(2026, 7, 1),
                last_date_invoiced=date(2026, 6, 30),
                recurring_next_date=date(2026, 7, 1),
            )
        mocked.assert_called_once_with(
            contract,
            last_date_invoiced=date(2026, 6, 30),
            recurring_next_date=date(2026, 7, 1),
        )

    def test_align_new_prepaid_uses_project_pff_without_last_date(self):
        contract = self.env["contract.contract"].new(
            {"recurring_invoicing_type": "pre-paid"}
        )
        with patch.object(
            type(self.selfconsumption), "_write_invoicing_dates_on_contract"
        ) as mocked:
            self.selfconsumption._align_new_contract_period_end(
                contract, period_recurring_next_date=date(2026, 7, 1)
            )
        mocked.assert_called_once_with(contract, recurring_next_date=date(2026, 7, 1))

    def test_prepaid_alta_stub_dates_use_wizard_date_to_period_end(self):
        stub_start, stub_end = self.selfconsumption._prepaid_alta_stub_dates(
            date(2026, 6, 25), date(2026, 6, 30)
        )
        self.assertEqual(stub_start, date(2026, 6, 25))
        self.assertEqual(stub_end, date(2026, 6, 30))

    def test_prepaid_alta_stub_dates_empty_when_after_period(self):
        stub_start, stub_end = self.selfconsumption._prepaid_alta_stub_dates(
            date(2026, 7, 1), date(2026, 6, 30)
        )
        self.assertFalse(stub_start)
        self.assertFalse(stub_end)

    def test_prepaid_baja_stub_dates_invoice_until_day_before_leave(self):
        stub_start, stub_end = self.selfconsumption._prepaid_baja_stub_dates(
            date(2026, 3, 31), date(2026, 6, 25)
        )
        self.assertEqual(stub_start, date(2026, 4, 1))
        self.assertEqual(stub_end, date(2026, 6, 24))

    def test_prepaid_baja_stub_dates_skip_when_already_invoiced_through_leave(self):
        stub_start, stub_end = self.selfconsumption._prepaid_baja_stub_dates(
            date(2026, 6, 30), date(2026, 6, 25)
        )
        self.assertFalse(stub_start)
        self.assertFalse(stub_end)

    def test_activate_prepaid_alta_invoices_stub_then_joins_next_period(self):
        contract = self.env["contract.contract"].new({})
        assignation = self.env["energy_selfconsumption.supply_point_assignation"].new(
            {}
        )
        self.selfconsumption.invoicing_mode = "power_acquired"
        self.selfconsumption.recurring_invoicing_type = "pre-paid"
        with patch.object(
            type(self.selfconsumption), "_invoice_power_acquired_stub"
        ) as invoice_stub, patch.object(
            type(self.selfconsumption), "_align_new_contract_period_end"
        ) as align:
            self.selfconsumption._activate_replacement_alta_contract(
                contract,
                assignation,
                execution_date=date(2026, 6, 25),
                period_recurring_next_date=date(2026, 7, 1),
                reference_last_date_invoiced=date(2026, 6, 30),
            )
        invoice_stub.assert_called_once_with(
            contract, assignation, date(2026, 6, 25), date(2026, 6, 30)
        )
        align.assert_called_once_with(
            contract,
            date(2026, 7, 1),
            last_date_invoiced=date(2026, 6, 30),
            recurring_next_date=date(2026, 7, 1),
        )

    def test_activate_postpaid_alta_does_not_invoice(self):
        contract = self.env["contract.contract"].new({})
        assignation = self.env["energy_selfconsumption.supply_point_assignation"].new(
            {}
        )
        self.selfconsumption.invoicing_mode = "energy_delivered"
        self.selfconsumption.recurring_invoicing_type = "post-paid"
        with patch.object(
            type(self.selfconsumption), "_invoice_power_acquired_stub"
        ) as invoice_stub, patch.object(
            type(self.selfconsumption), "_align_new_contract_period_end"
        ) as align:
            self.selfconsumption._activate_replacement_alta_contract(
                contract,
                assignation,
                execution_date=date(2026, 5, 3),
                period_recurring_next_date=date(2026, 7, 1),
                reference_last_date_invoiced=date(2026, 5, 2),
            )
        invoice_stub.assert_not_called()
        align.assert_called_once_with(
            contract,
            date(2026, 7, 1),
            last_date_invoiced=False,
            recurring_next_date=date(2026, 7, 1),
        )

    def test_last_date_invoiced_dropped_when_before_new_start(self):
        self.assertFalse(
            self.selfconsumption._last_date_invoiced_for_new_contract(
                date(2026, 5, 2), date(2026, 5, 3)
            )
        )

    def test_last_date_invoiced_kept_when_on_or_after_new_start(self):
        self.assertEqual(
            self.selfconsumption._last_date_invoiced_for_new_contract(
                date(2026, 6, 30), date(2026, 6, 25)
            ),
            date(2026, 6, 30),
        )

    def test_close_date_for_replacement_cannot_precede_last_invoice(self):
        contract = self.env["contract.contract"].new(
            {"last_date_invoiced": date(2026, 6, 30)}
        )
        self.assertEqual(
            self.selfconsumption._close_date_for_replacement(
                contract, date(2026, 6, 24)
            ),
            date(2026, 6, 30),
        )

    def test_leave_prepaid_skips_invoice_when_already_billed(self):
        contract = self.env["contract.contract"].new(
            {"last_date_invoiced": date(2026, 6, 30)}
        )
        assignation = self.env["energy_selfconsumption.supply_point_assignation"].new(
            {}
        )
        self.selfconsumption.invoicing_mode = "power_acquired"
        self.selfconsumption.recurring_invoicing_type = "pre-paid"
        with patch.object(
            type(self.selfconsumption), "_invoice_power_acquired_stub"
        ) as invoice_stub, patch(
            "odoo.addons.energy_selfconsumption.models.selfconsumption.contract_utils"
        ) as mocked_utils:
            component = mocked_utils.return_value.__enter__.return_value
            self.selfconsumption._leave_contract_on_replacement(
                contract, assignation, date(2026, 6, 25)
            )
        invoice_stub.assert_not_called()
        component.close.assert_called_once_with(date(2026, 6, 30))

    def test_leave_prepaid_invoices_unbilled_stub(self):
        contract = self.env["contract.contract"].new(
            {"last_date_invoiced": date(2026, 3, 31)}
        )
        assignation = self.env["energy_selfconsumption.supply_point_assignation"].new(
            {}
        )
        self.selfconsumption.invoicing_mode = "power_acquired"
        self.selfconsumption.recurring_invoicing_type = "pre-paid"
        with patch.object(
            type(self.selfconsumption), "_invoice_power_acquired_stub"
        ) as invoice_stub, patch(
            "odoo.addons.energy_selfconsumption.models.selfconsumption.contract_utils"
        ) as mocked_utils:
            component = mocked_utils.return_value.__enter__.return_value
            self.selfconsumption._leave_contract_on_replacement(
                contract, assignation, date(2026, 6, 25)
            )
        invoice_stub.assert_called_once_with(
            contract, assignation, date(2026, 4, 1), date(2026, 6, 24)
        )
        component.close.assert_called_once_with(date(2026, 6, 24))

    def _new_assignation(self, supply_point, project=None):
        table = self.env["energy_selfconsumption.distribution_table"].new(
            {
                "selfconsumption_project_id": project or self.selfconsumption,
            }
        )
        return self.env["energy_selfconsumption.supply_point_assignation"].new(
            {
                "distribution_table_id": table,
                "supply_point_id": supply_point,
            }
        )

    def _demo_or_search_inscription(self, xmlid, domain=None):
        inscription = self.env.ref(xmlid, raise_if_not_found=False)
        if inscription:
            return inscription
        domain = list(domain or [])
        domain.append(("selfconsumption_project_id", "=", self.selfconsumption.id))
        inscription = self.env[
            "energy_selfconsumption.inscription_selfconsumption"
        ].search(domain, limit=1)
        if not inscription:
            self.skipTest("No self-consumption inscription available")
        return inscription

    def test_inscription_for_assignation_uses_cups_not_partner(self):
        inscription = self._demo_or_search_inscription(
            "energy_selfconsumption.inscription_selfconsumption_1_selfconsumption_1_demo",
            [("supply_point_id", "!=", False)],
        )
        assignation = self._new_assignation(inscription.supply_point_id)
        found = self.selfconsumption._get_inscription_for_assignation(assignation)
        self.assertEqual(found, inscription)
        self.assertEqual(found.supply_point_id, inscription.supply_point_id)

    def test_inscription_for_assignation_raises_when_missing(self):
        cups_code = "ES0031607584576001MM0F"
        supply_point = self.env["energy_selfconsumption.supply_point"].new(
            {"code": cups_code}
        )
        assignation = self._new_assignation(supply_point)
        with self.assertRaises(ValidationError) as error:
            self.selfconsumption._get_inscription_for_assignation(assignation)
        self.assertIn(cups_code, str(error.exception))

    def test_inscription_mandate_id_uses_cups_inscription(self):
        inscription = self._demo_or_search_inscription(
            "energy_selfconsumption.inscription_selfconsumption_1_selfconsumption_1_demo",
            [("mandate_id", "!=", False), ("supply_point_id", "!=", False)],
        )
        if not inscription.mandate_id:
            self.skipTest("No inscription with mandate available")
        mandate_id = self.selfconsumption._get_inscription_mandate_id(
            inscription, inscription.supply_point_id
        )
        self.assertEqual(mandate_id, inscription.mandate_id.id)

    def test_inscription_mandate_id_does_not_merge_partner_inscriptions(self):
        first = self._demo_or_search_inscription(
            "energy_selfconsumption.inscription_selfconsumption_1_selfconsumption_1_demo",
            [("mandate_id", "!=", False), ("supply_point_id", "!=", False)],
        )
        second = self.env.ref(
            "energy_selfconsumption.inscription_selfconsumption_2_selfconsumption_1_demo",
            raise_if_not_found=False,
        )
        if not second:
            second = self.env[
                "energy_selfconsumption.inscription_selfconsumption"
            ].search(
                [
                    ("id", "!=", first.id),
                    ("mandate_id", "!=", False),
                    ("supply_point_id", "!=", False),
                    (
                        "selfconsumption_project_id",
                        "=",
                        self.selfconsumption.id,
                    ),
                ],
                limit=1,
            )
        if not second or not second.mandate_id:
            self.skipTest("Need two inscriptions with mandate")
        if first.mandate_id == second.mandate_id:
            self.skipTest("Inscriptions share the same mandate")
        mandate_id = self.selfconsumption._get_inscription_mandate_id(
            first | second, first.supply_point_id
        )
        self.assertEqual(mandate_id, first.mandate_id.id)

    def test_inscription_mandate_id_raises_with_cups_when_missing(self):
        cups_code = "ES0031607584576001MM0F"
        partner = self.env["res.partner"].create({"name": "Cobiella"})
        inscription = self.env["energy_project.inscription"].new(
            {"partner_id": partner.id}
        )
        supply_point = self.env["energy_selfconsumption.supply_point"].new(
            {"code": cups_code}
        )
        with self.assertRaises(ValidationError) as error:
            self.selfconsumption._get_inscription_mandate_id(inscription, supply_point)
        self.assertIn(cups_code, str(error.exception))
        self.assertIn("Cobiella", str(error.exception))

    def test_inscription_mandate_id_optional_returns_none(self):
        inscription = self.env["energy_project.inscription"].new({})
        supply_point = self.env["energy_selfconsumption.supply_point"].new(
            {"code": "ES0031607584576001MM0F"}
        )
        self.assertIsNone(
            self.selfconsumption._get_inscription_mandate_id(
                inscription, supply_point, required=False
            )
        )

    def test_existing_pack_contract_filters_by_cups(self):
        supply_points = self.env["energy_selfconsumption.supply_point"].search(
            [], limit=2
        )
        if not supply_points:
            self.skipTest("No supply point available")
        supply_point = supply_points[0]
        partner = supply_point.partner_id or self.env["res.partner"].search([], limit=1)
        with patch(
            "odoo.addons.energy_selfconsumption.models.selfconsumption.get_existing_pack_contract"
        ) as mocked:
            mocked.return_value = self.env["contract.contract"]
            self.selfconsumption._get_existing_pack_contract_for_supply_point(
                partner, supply_point, ["in_progress"]
            )
            extra_query = mocked.call_args[0][4]
            self.assertIn(
                (
                    "supply_point_assignation_id.supply_point_id",
                    "=",
                    supply_point.id,
                ),
                extra_query,
            )
            if len(supply_points) > 1:
                self.assertNotIn(
                    (
                        "supply_point_assignation_id.supply_point_id",
                        "=",
                        supply_points[1].id,
                    ),
                    extra_query,
                )

    def test_existing_pack_contract_empty_when_partner_or_cups_missing(self):
        supply_point = self.env["energy_selfconsumption.supply_point"].search(
            [], limit=1
        )
        if not supply_point:
            self.skipTest("No supply point available")
        self.assertFalse(
            self.selfconsumption._get_existing_pack_contract_for_supply_point(
                self.env["res.partner"], supply_point, ["in_progress"]
            )
        )
        partner = supply_point.partner_id or self.env["res.partner"].search([], limit=1)
        self.assertFalse(
            self.selfconsumption._get_existing_pack_contract_for_supply_point(
                partner,
                self.env["energy_selfconsumption.supply_point"],
                ["in_progress"],
            )
        )

    def _two_active_inscriptions_different_partners(self):
        inscriptions = self.env[
            "energy_selfconsumption.inscription_selfconsumption"
        ].search(
            [
                ("state", "=", INSCRIPTION_STATE_ACTIVE),
                ("supply_point_id", "!=", False),
                ("selfconsumption_project_id", "!=", False),
            ]
        )
        by_project = {}
        for inscription in inscriptions:
            by_project.setdefault(inscription.selfconsumption_project_id.id, []).append(
                inscription
            )
        for project_inscriptions in by_project.values():
            first = project_inscriptions[0]
            for second in project_inscriptions[1:]:
                if (
                    second.partner_id != first.partner_id
                    and second.supply_point_id != first.supply_point_id
                ):
                    return first, second
        self.skipTest("Need two active inscriptions with different partners and CUPS")

    def test_unique_active_inscription_per_project_cups(self):
        first, second = self._two_active_inscriptions_different_partners()
        with self.assertRaises(ValidationError) as error:
            second.with_context(lang="en_US").write(
                {"supply_point_id": first.supply_point_id.id}
            )
        self.assertIn("already an active inscription", str(error.exception))
        cups_code = first.supply_point_id.code
        if cups_code:
            self.assertIn(cups_code, str(error.exception))

    def test_get_inscription_prefers_active_cups(self):
        first, second = self._two_active_inscriptions_different_partners()
        second.write({"state": INSCRIPTION_STATE_CANCELLED})
        second.write({"supply_point_id": first.supply_point_id.id})
        assignation = self._new_assignation(
            first.supply_point_id, project=first.selfconsumption_project_id
        )
        found = assignation.get_inscription()
        self.assertEqual(found, first)
        self.assertEqual(found.state, INSCRIPTION_STATE_ACTIVE)
