from odoo.tests.common import TransactionCase


class TestSeriveInvoicingActionCreate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_demo_data_creation_ok(self):
        # check data creation successful
        self.assertEqual(
            self.env.ref(
                "energy_communities_service_invoicing.demo_platform_service_product_template"
            ).name,
            "Platform service product",
        )
        self.assertEqual(
            self.env.ref(
                "energy_communities_service_invoicing.demo_platform_pack_product_template"
            ).name,
            "Platform pack product",
        )
        self.assertEqual(
            self.env.ref(
                "energy_communities_service_invoicing.demo_platform_pack_contract_template"
            ).name,
            "Platform pack contract template",
        )
