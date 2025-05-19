from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)


@tagged("-at_install", "post_install", "energy_selfconsumption")
class TestSeriveInvoicingContractGeneration(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.selfconsumption = self.env.ref(
            "energy_selfconsumption.selfconsumption_1_community_1_demo"
        )

    def test_contract_generation_wizard(self):
        # pack_product = self.env.ref("energy_selfconsumption.product_product_power_acquired_product_pack_template")
        # pack_product = self.env.ref("energy_selfconsumption.product_product_energy_delivered_product_pack_template")
        pack_product = self.env.ref(
            "energy_selfconsumption.product_product_energy_custom_product_pack_template"
        )
        # WORKFLOW: invoicing mode execution
        invoice_mode_wizard = self.env[
            "energy_selfconsumption.define_invoicing_mode.wizard"
        ].create(
            {
                "selfconsumption_id": self.selfconsumption.id,
                # "invoicing_mode": "power_acquired",
                # "invoicing_mode": "energy_delivered",
                "invoicing_mode": "energy_custom",
                "price": 11,
                "recurring_rule_type": "quarterly",
                "recurring_interval": 2,
                "recurring_invoicing_type": "post-paid",
            }
        )
        invoice_mode_wizard.create_contract_template()
        sale_orders = self.selfconsumption.get_sale_orders()
        # CHECK: only one sale order created
        self.assertEqual(len(sale_orders), 5)
        # CHECK: Sale order has metadata for recurring_rule_type
        meta_recurring_rule_type = sale_orders.metadata_line_ids.filtered(
            lambda metadata: metadata.key == "recurring_rule_type"
            and metadata.order_id == sale_orders[0]
        )
        self.assertEqual(True, bool(meta_recurring_rule_type))
        self.assertEqual(
            invoice_mode_wizard.recurring_rule_type, meta_recurring_rule_type.value
        )
        # CHECK: Sale order has metadata for recurring_interval
        meta_recurring_interval = sale_orders.metadata_line_ids.filtered(
            lambda metadata: metadata.key == "recurring_interval"
            and metadata.order_id == sale_orders[0]
        )
        self.assertEqual(True, bool(meta_recurring_interval))
        self.assertEqual(
            str(invoice_mode_wizard.recurring_interval), meta_recurring_interval.value
        )
        # CHECK: Sale order has metadata for recurring_invoicing_type
        meta_recurring_invoicing_type = sale_orders.metadata_line_ids.filtered(
            lambda metadata: metadata.key == "recurring_invoicing_type"
            and metadata.order_id == sale_orders[0]
        )
        self.assertEqual(True, bool(meta_recurring_invoicing_type))
        self.assertEqual(
            invoice_mode_wizard.recurring_invoicing_type,
            meta_recurring_invoicing_type.value,
        )
        # CHECK: Sale order has no date_end
        self.assertEqual(
            sale_orders[0].order_line[0].date_start,
            sale_orders[0].order_line[0].date_end,
        )
        # CHECK: project product defined correctly
        self.assertEqual(
            self.selfconsumption.product_id.id, pack_product.product_variant_id.id
        )
        # CHECK: project has same product as sale order
        self.assertEqual(
            self.selfconsumption.product_id.id,
            sale_orders[0].order_line[0].product_id.id,
        )
        # CHECK: project has same contract template as sale order
        self.assertEqual(
            self.selfconsumption.contract_template_id.id,
            sale_orders[0].order_line[0].product_id.property_contract_template_id.id,
        )
        # CHECK: project invoicing mode correctly defined
        self.assertEqual(
            invoice_mode_wizard.invoicing_mode, self.selfconsumption.invoicing_mode
        )
        # CHECK: project has recurring_rule_type correctly defined
        self.assertEqual(
            invoice_mode_wizard.recurring_rule_type,
            self.selfconsumption.recurring_rule_type,
        )
        # CHECK: project has recurring_interval correctly defined
        self.assertEqual(
            invoice_mode_wizard.recurring_interval,
            self.selfconsumption.recurring_interval,
        )
        # CHECK: project has recurring_invoicing_type correctly defined
        self.assertEqual(
            invoice_mode_wizard.recurring_invoicing_type,
            self.selfconsumption.recurring_invoicing_type,
        )
        # CHECK: project has pricelist_id correctly defined
        self.assertEqual(
            sale_orders[0].pricelist_id.id, self.selfconsumption.pricelist_id.id
        )
        # CHECK pricelist_id properly defined
        self.assertEqual(1, len(self.selfconsumption.pricelist_id.item_ids))
        self.assertEqual(
            pack_product.property_contract_template_id.contract_line_ids[
                0
            ].product_id.id,
            self.selfconsumption.pricelist_id.item_ids[0].product_id.id,
        )
        self.assertEqual(
            invoice_mode_wizard.price,
            self.selfconsumption.pricelist_id.item_ids[0].fixed_price,
        )

        #  WORKFLOW: Contract generation execution
        contract_create_wizard = self.env[
            "energy_selfconsumption.contract_generation.wizard"
        ].create(
            {
                "selfconsumption_id": self.selfconsumption.id,
                "payment_mode": self.ref(
                    "account_banking_sepa_direct_debit.payment_mode_inbound_sepa_dd1"
                ),
            }
        )
        contract_create_wizard.action_generate_contracts()
        contracts = self.selfconsumption.get_contracts()
        contract = contracts[0]
        # CHECK: only one generated contract
        self.assertEqual(len(contracts), 5)
        # CHECK: sale order "confirmed"
        self.assertEqual(sale_orders[0].state, "sale")
        # CHECK: contract has line recurrence
        self.assertEqual(contract.line_recurrence, True)
        # CHECK: contract pack_type is selfconsumption
        self.assertEqual(contract.pack_type, "selfconsumption_pack")
        # CHECK: contract contract_template same as project contract_template
        self.assertEqual(
            contract.contract_template_id.id,
            self.selfconsumption.contract_template_id.id,
        )
        # CHECK: contract product uses pricelist
        self.assertEqual(contract.contract_line_ids[0].automatic_price, True)
        # CHECK: contract product same as project product
        self.assertEqual(
            contract.contract_line_ids[0].product_id.id,
            self.selfconsumption.contract_template_id.contract_line_ids[
                0
            ].product_id.id,
        )
        # CHECK: contract qty_type same as project
        self.assertEqual(
            contract.contract_line_ids[0].qty_type,
            self.selfconsumption.contract_template_id.contract_line_ids[0].qty_type,
        )
        # CHECK: contract qty_formula_id in same as project
        self.assertEqual(
            contract.contract_line_ids[0].qty_formula_id.id,
            self.selfconsumption.contract_template_id.contract_line_ids[
                0
            ].qty_formula_id.id,
        )
        # CHECK: contract uom_id same as project
        self.assertEqual(
            contract.contract_line_ids[0].uom_id.id,
            self.selfconsumption.contract_template_id.contract_line_ids[0].uom_id.id,
        )
        # CHECK: contract recurring_rule_type same as project
        self.assertEqual(
            contract.contract_line_ids[0].recurring_rule_type,
            self.selfconsumption.recurring_rule_type,
        )
        # CHECK: contract recurring_interval same as project
        self.assertEqual(
            contract.contract_line_ids[0].recurring_interval,
            self.selfconsumption.recurring_interval,
        )
        # CHECK: contract recurring_invoicing_type same as project
        self.assertEqual(
            contract.contract_line_ids[0].recurring_invoicing_type,
            self.selfconsumption.recurring_invoicing_type,
        )
        # CHECK: contract date_start same as sale order
        self.assertEqual(
            contract.contract_line_ids[0].date_start.strftime("%Y-%m-%d"),
            sale_orders[0].commitment_date.strftime("%Y-%m-%d"),
        )
        self.assertEqual(
            contract.date_start.strftime("%Y-%m-%d"),
            sale_orders[0].commitment_date.strftime("%Y-%m-%d"),
        )
        # TODO: check this only for prepayment contracts??
        # CHECK: contract recurring_next_date same as sale order
        # self.assertEqual(
        #     contract.contract_line_ids[0].recurring_next_date.strftime("%Y-%m-%d"),
        #     sale_orders.commitment_date.strftime("%Y-%m-%d")
        # )
        # CHECK: contract date_end not defined
        self.assertEqual(contract.contract_line_ids[0].date_end, False)
        self.assertEqual(contract.date_end, False)
        # CHECK: contract pricelist_id same as sale_order
        self.assertEqual(contract.pricelist_id.id, sale_orders[0].pricelist_id.id)
        # CHECK: contract pricelist_id same as project
        self.assertEqual(contract.pricelist_id.id, self.selfconsumption.pricelist_id.id)
        # CHECK: contract payment_mode same as sale_order
        self.assertEqual(contract.payment_mode_id.id, sale_orders[0].payment_mode_id.id)
        # CHECK: contract payment_mode correctly defined
        self.assertEqual(
            contract.payment_mode_id.id, contract_create_wizard.payment_mode.id
        )
