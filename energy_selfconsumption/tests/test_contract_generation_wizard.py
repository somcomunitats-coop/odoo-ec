from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestContractGenerationWizard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "test partner"})
        self.selfconsumption = self.env[
            "energy_selfconsumption.selfconsumption"
        ].create(
            {
                "name": "test Selfconsumption Project",
                "type": self.env.ref(
                    "energy_selfconsumption.selfconsumption_project_type"
                ).id,
                "code": "ES0397277816188340VL",
                "cil": "001ES0397277816188340VL",
                "state": "activation",
                "power": 100,
                "street": "Carrer de Sants, 79",
                "zip": "08014",
                "city": "Barcelona",
                "state_id": self.env.ref("base.state_es_b").id,
                "country_id": self.env.ref("base.es").id,
            }
        )
        self.inscription = self.env["energy_project.inscription"].create(
            {
                "project_id": self.selfconsumption.project_id.id,
                "partner_id": self.partner.id,
                "effective_date": datetime.today(),
            }
        )
        self.supply_point = self.env["energy_selfconsumption.supply_point"].create(
            {
                "code": "ES0029542181297829TM",
                "street": "C. de Sta. Catalina",
                "street2": "55º B",
                "zip": "08014",
                "city": "Barcelona",
                "state_id": self.env.ref("base.state_es_b").id,
                "country_id": self.env.ref("base.es").id,
                "owner_id": self.partner.id,
                "partner_id": self.partner.id,
            }
        )
        self.distribution_table = self.env[
            "energy_selfconsumption.distribution_table"
        ].create(
            {
                "name": "DT001",
                "selfconsumption_project_id": self.selfconsumption.id,
                "type": "fixed",
                "state": "process",
            }
        )
        self.supply_point_assignation = self.env[
            "energy_selfconsumption.supply_point_assignation"
        ].create(
            {
                "distribution_table_id": self.distribution_table.id,
                "supply_point_id": self.supply_point.id,
                "coefficient": 1,
            }
        )
        self.define_invoicing_mode_power_acquired_wizard = self.env[
            "energy_selfconsumption.define_invoicing_mode.wizard"
        ].create(
            {
                "selfconsumption_id": self.selfconsumption.id,
                "price": 0.1,
                "recurring_interval": 1,
                "recurring_rule_type": "monthly",
                "invoicing_mode": "power_acquired",
            }
        )
        self.define_invoicing_mode_energy_delivered_wizard = self.env[
            "energy_selfconsumption.define_invoicing_mode.wizard"
        ].create(
            {
                "selfconsumption_id": self.selfconsumption.id,
                "price": 0.1,
                "recurring_interval": 1,
                "recurring_rule_type": "monthly",
                "invoicing_mode": "energy_delivered",
            }
        )
        self.contract_generation_wizard = self.env[
            "energy_selfconsumption.contract_generation.wizard"
        ].create(
            {
                "selfconsumption_id": self.selfconsumption.id,
            }
        )

    def test_power_acquired_generation_contracts(self):
        res = (
            self.define_invoicing_mode_power_acquired_wizard.save_data_to_selfconsumption()
        )
        self.assertEqual(
            res,
            {
                "type": "ir.actions.act_window_close",
            },
        )

        res = self.contract_generation_wizard.generate_contracts_button()
        self.assertEqual(res, True)

        related_contract = self.env["contract.contract"].search(
            [("project_id", "=", self.selfconsumption.project_id.id)]
        )
        contract_line = related_contract[0].contract_line_ids[0]
        days_timedelta = (
            contract_line.next_period_date_end - contract_line.next_period_date_start
        )
        expected_quantity = 100 * 1 * (days_timedelta.days + 1)
        related_contract[0].recurring_create_invoice()
        invoice = related_contract._get_related_invoices()
        self.assertEqual(invoice.invoice_line_ids[0].quantity, expected_quantity)
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 0.1)

    def test_energy_delivered_generation_contracts(self):
        res = (
            self.define_invoicing_mode_energy_delivered_wizard.save_data_to_selfconsumption()
        )
        self.assertEqual(
            res,
            {
                "type": "ir.actions.act_window_close",
            },
        )

        res = self.contract_generation_wizard.generate_contracts_button()
        self.assertEqual(res, True)

        related_contract = self.env["contract.contract"].search(
            [("project_id", "=", self.selfconsumption.project_id.id)]
        )

        wizard_id = self.env["energy_selfconsumption.invoicing.wizard"].create(
            {
                "contract_ids": [(6, 0, related_contract.ids)],
                "power": 200,
            }
        )

        expected_quantity = 200 * 1
        wizard_id.generate_invoices()
        invoice = related_contract._get_related_invoices()
        self.assertEqual(invoice.invoice_line_ids[0].quantity, expected_quantity)
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 0.1)
