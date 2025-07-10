from datetime import date, datetime, timedelta
from unittest import skip
from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "standard", "-at_install", "energy_selfconsumption")
class TestInvoicingReminder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.selfconsumption_import_wizard = self.env[
            "energy_selfconsumption.selfconsumption_import.wizard"
        ].create({})
        self.company = self.env["res.company"].search([], limit=1)[0]
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
                "invoicing_mode": "energy_delivered",
            }
        )
        self.inscription = self.env["energy_project.inscription"].create(
            {
                "project_id": self.selfconsumption.project_id.id,
                "partner_id": self.partner.id,
                "effective_date": datetime.today(),
                "mandate_id": self.mandate.id,
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
        self.define_invoicing_mode_wizard = self.env[
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

    @skip("This test must be adapted to new service invoicing structure")
    def test_send_energy_delivery_invoicing_reminder(self):
        # Test using send_energy_delivery_invoicing_reminder() method to send
        # correctly email
        validation_date = date.today() + timedelta(days=3)
        self.define_invoicing_mode_wizard.save_data_to_selfconsumption()
        self.contract_generation_wizard.generate_contracts_button()
        contract = self.env["contract.contract"].search(
            [("project_id", "=", self.selfconsumption.project_id.id)]
        )
        contract.recurring_next_date = validation_date
        with patch.object(
            type(self.selfconsumption), "message_post_with_template", MagicMock()
        ) as mock_message_post:
            contract.recurring_next_date = validation_date - timedelta(days=1)
            self.selfconsumption.send_energy_delivery_invoicing_reminder()
            mock_message_post.assert_called()
