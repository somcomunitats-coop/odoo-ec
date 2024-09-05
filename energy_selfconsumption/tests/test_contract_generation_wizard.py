import base64
from datetime import datetime

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "energy_selfconsumption")
class TestContractGenerationWizard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.selfconsumption_import_wizard = self.env[
            "energy_selfconsumption.selfconsumption_import.wizard"
        ].create({})
        self.company = self.env["res.company"].search(
            [("name", "=", "Som Comunitats")]
        )[0]
        self.partner = self.env["res.partner"].create(
            {
                "name": f"Test Partner",
                "vat": self.selfconsumption_import_wizard.generar_vat_espanol(),
                "country_id": self.env.ref("base.es").id,
                "state_id": self.env.ref("base.state_es_b").id,
                "street": f"Carrer de Sants, 79",
                "city": "Barcelona",
                "zip": "08014",
                "type": "contact",
                "company_id": self.company.id,
                "company_type": "person",
                "cooperative_membership_id": self.company.partner_id.id,
            }
        )
        self.bank_account = self.env["res.partner.bank"].create(
            {
                "acc_number": self.selfconsumption_import_wizard.generar_iban_espanol(),
                "partner_id": self.partner.id,
                "company_id": self.company.id,
            }
        )
        self.mandate = self.env["account.banking.mandate"].create(
            {
                "format": "sepa",
                "type": "recurrent",
                "state": "valid",
                "signature_date": datetime.now().strftime("%Y-%m-%d"),
                "partner_bank_id": self.bank_account.id,
                "partner_id": self.partner.id,
                "company_id": self.company.id,
            }
        )
        self.selfconsumption = self.env[
            "energy_selfconsumption.selfconsumption"
        ].create(
            {
                "name": "test Selfconsumption Project",
                "type": self.env.ref(
                    "energy_selfconsumption.selfconsumption_project_type"
                ).id,
                "code": "ES0021119448300637FDA009",
                "cil": "ES0021119448300637FD009",
                "state": "activation",
                "power": 100,
                "street": "Carrer de Sants, 79",
                "zip": "08014",
                "city": "Barcelona",
                "state_id": self.env.ref("base.state_es_b").id,
                "country_id": self.env.ref("base.es").id,
                "company_id": self.company.id,
            }
        )
        self.inscription = self.env["energy_project.inscription"].create(
            {
                "project_id": self.selfconsumption.project_id.id,
                "partner_id": self.partner.id,
                "effective_date": datetime.today(),
                "mandate_id": self.mandate.id,
                "company_id": self.company.id,
            }
        )
        self.supply_point = self.env["energy_selfconsumption.supply_point"].create(
            {
                "code": self.selfconsumption_import_wizard.generate_cups(),
                "street": "C. de Sta. Catalina",
                "street2": "55º B",
                "zip": "08014",
                "city": "Barcelona",
                "state_id": self.env.ref("base.state_es_b").id,
                "country_id": self.env.ref("base.es").id,
                "owner_id": self.partner.id,
                "partner_id": self.partner.id,
                "company_id": self.company.id,
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
                "company_id": self.company.id,
            }
        )
        self.supply_point_assignation = self.env[
            "energy_selfconsumption.supply_point_assignation"
        ].create(
            {
                "distribution_table_id": self.distribution_table.id,
                "supply_point_id": self.supply_point.id,
                "coefficient": 1,
                "company_id": self.company.id,
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
        self.define_invoicing_mode_energy_delivered_custom_wizard = self.env[
            "energy_selfconsumption.define_invoicing_mode.wizard"
        ].create(
            {
                "selfconsumption_id": self.selfconsumption.id,
                "price": 0.1,
                "recurring_interval": 1,
                "recurring_rule_type": "monthly",
                "invoicing_mode": "energy_custom",
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

        contract_line = related_contract[0].get_main_line()
        # This variable must be queried for the tests to work.
        a = contract_line.date_start
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
        # This variable must be queried for the tests to work.
        a = related_contract[0].date_start

        wizard_id = (
            self.env["energy_selfconsumption.invoicing.wizard"]
            .with_context({"active_ids": related_contract.ids})
            .create(
                {
                    "contract_ids": [(6, 0, related_contract.ids)],
                    "power": 200,
                }
            )
        )

        expected_quantity = 200 * 1
        wizard_id.generate_invoices()
        invoice = related_contract._get_related_invoices()
        self.assertEqual(invoice.invoice_line_ids[0].quantity, expected_quantity)
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 0.1)

    def test_energy_delivered_custom_generation_contracts(self):
        res = (
            self.define_invoicing_mode_energy_delivered_custom_wizard.save_data_to_selfconsumption()
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

        # Simular el contenido del informe CSV
        csv_content = "CUPS,Energia a facturar (kWh),CAU,Periode facturat start (dd/mm/aaaa),Periode facturat end (dd/mm/aaaa)\n"
        for contract in related_contract:
            main_line = contract.get_main_line()
            # This variable must be queried for the tests to work.
            a = main_line.date_start
            next_period_date_start = (
                main_line.next_period_date_start
                if main_line
                else contract.contract_line_ids[0].next_period_date_start
            )
            next_period_date_end = (
                main_line.next_period_date_end
                if main_line
                else contract.contract_line_ids[0].next_period_date_end
            )
            csv_content += f"{contract.supply_point_assignation_id.supply_point_id.code},\"0,019\",{contract.project_id.selfconsumption_id.code},{next_period_date_start.strftime('%d/%m/%Y')},{next_period_date_end.strftime('%d/%m/%Y')}"
        # Codificar el contenido en base64
        csv_content_base64 = base64.b64encode(csv_content.encode("utf-8")).decode(
            "utf-8"
        )

        wizard_id = (
            self.env["energy_selfconsumption.invoicing.wizard"]
            .with_context({"active_ids": related_contract.ids})
            .create(
                {
                    "contract_ids": [(6, 0, related_contract.ids)],
                    "import_file": csv_content_base64,
                    "fname": "test.csv",
                }
            )
        )
        wizard_id.generate_invoices()
        invoice = related_contract._get_related_invoices()
        self.assertEqual(invoice.invoice_line_ids[0].quantity, 0.02)
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 0.1)
