from datetime import date, datetime, timedelta

from odoo.tests import TransactionCase


class TestInvoicingReminder(TransactionCase):
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
                "invoicing_mode": "energy_delivered",
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

    def test_send_energy_delivery_invoicing_reminder(self):
        # Test using send_energy_delivery_invoicing_reminder() method to send correctly email
        validation_date = date.today() + timedelta(days=3)
        self.define_invoicing_mode_wizard.save_data_to_selfconsumption()
        self.contract_generation_wizard.generate_contracts_button()
        contract = self.env["contract.contract"].search(
            [("name", "=", "Contract - test Selfconsumption Project - test partner")]
        )
        contract.recurring_next_date = validation_date

        self.env[
            "energy_selfconsumption.selfconsumption"
        ].send_energy_delivery_invoicing_reminder()
        reminder_mail = self.env["mail.mail"].search(
            [("subject", "=", "Selfconsumption - Energy Delivered Invoicing Reminder")]
        )
        self.assertTrue(reminder_mail, "El correo de recordatorio no se envió.")

        # Delete sent email to make other test
        reminder_mail.unlink()

        # Test using the send_energy_delivery_invoicing_reminder() method with a record with a date outside the parameter (3 days)
        contract.recurring_next_date = validation_date + timedelta(days=1)
        self.env[
            "energy_selfconsumption.selfconsumption"
        ].send_energy_delivery_invoicing_reminder()
        reminder_mail = self.env["mail.mail"].search(
            [("subject", "=", "Selfconsumption - Energy Delivered Invoicing Reminder")]
        )
        self.assertFalse(reminder_mail, "El correo de recordatorio no se envió.")
