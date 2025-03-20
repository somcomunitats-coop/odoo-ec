from odoo.tests.common import TransactionCase


class TestSeriveInvoicingActionCreate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_demo_data_creation_ok(self):
        # check data creation successful
        platform_pack_product = self.env.ref(
            "energy_communities_service_invoicing.demo_platform_pack_product_template"
        )
        self.assertEqual(
            platform_pack_product.name, "Pack product for platform service invoicing"
        )
        # TODO: check contract template data properly created
        # platform_pack_contract = self.env
        # self.assertEqual()
