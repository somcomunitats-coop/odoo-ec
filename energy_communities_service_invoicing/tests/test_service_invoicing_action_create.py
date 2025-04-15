import re
import unittest

from dateutil.relativedelta import relativedelta

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)


@tagged("-at_install", "post_install")
class TestSeriveInvoicingActionCreate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    @unittest.skip("skip")
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

    def test_contract_recurrency_ok(self):
        # One project with one contract
        selfconsumption_project = self.env[
            "energy_selfconsumption.selfconsumption"
        ].search([("id", "=", 25)])
        contract = self.env["contract.contract"].search([("id", "=", 14)])[0]
        self.assertTrue(bool(contract.recurring_next_date))
        # Get make a price list
        price = contract.contract_line_ids[0].price_unit
        product_template = self.env.ref(
            "energy_selfconsumption.product_product_energy_delivered_product_template"
        )
        pricelist = self.env["product.pricelist"].create(
            {
                "name": f"{selfconsumption_project.name} {selfconsumption_project.invoicing_mode} Selfconsumption Pricelist",
                "company_id": selfconsumption_project.company_id.id,
                "currency_id": selfconsumption_project.company_id.currency_id.id,
                "discount_policy": "without_discount",
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "base": "standard_price",
                            "product_tmpl_id": product_template.id,
                            "product_id": product_template.product_variant_id.id,
                            "compute_price": "fixed",
                            "fixed_price": price,
                            "categ_id": self.env.ref(
                                "energy_selfconsumption.product_category_selfconsumption_service"
                            ).id,
                        },
                    )
                ],
            }
        )
        # Giveme a pack
        pack = self.env.ref(
            "energy_selfconsumption.product_product_energy_delivered_product_pack_template"
        )
        # Get payment mode
        payment_mode = self.env["account.payment.mode"].search(
            [
                ("company_id", "=", selfconsumption_project.company_id.id),
                ("payment_type", "=", "inbound"),
            ]
        )
        # Get journal
        journal_id = self.env["account.journal"].search(
            [
                ("company_id", "=", selfconsumption_project.company_id.id),
                ("type", "=", "sale"),
            ],
            limit=1,
        )
        contract_cups = contract.contract_line_ids[0].name
        match = re.search(r"CUPS:\s*(\S+)", contract_cups)
        if match:
            contract_cups = match.group(1)
            supply_point_id = self.env["energy_selfconsumption.supply_point"].search(
                [("code", "=", contract_cups)]
            )

        with contract_utils(self.env, contract) as component:
            component.set_contract_status_closed(contract.last_date_invoiced)
            self.assertTrue(bool(contract.recurring_next_date))
            service_invoicing_id = component.reopen(
                contract.last_date_invoiced,
                pricelist,
                pack,
                False,
                payment_mode[0],
                {
                    "selfconsumption_id": selfconsumption_project.id,
                    "supply_point_id": supply_point_id.id,
                    "recurring_interval": contract.recurring_interval,
                    "recurring_rule_type": contract.recurring_rule_type,
                    "recurring_invoicing_type": contract.recurring_invoicing_type,
                    "last_date_invoiced": contract.last_date_invoiced,
                    "journal_id": journal_id.id,
                    "project_id": selfconsumption_project.id,
                    "company_id": selfconsumption_project.company_id.id,
                },
            )
            self.assertTrue(bool(contract.recurring_next_date))
        with contract_utils(self.env, service_invoicing_id) as component:
            component.set_contract_status_active(contract.last_date_invoiced)

        self.assertEqual(service_invoicing_id.status, "in_progress")
        self.assertEqual(service_invoicing_id.date_start, contract.last_date_invoiced)
        self.assertEqual(contract.date_end, contract.last_date_invoiced)
        self.assertEqual(service_invoicing_id.recurring_next_date, contract.recurring_next_date)
        self.assertEqual(service_invoicing_id.contract_line_ids[0].recurring_next_date, contract.contract_line_ids[0].recurring_next_date)
        self.assertEqual(service_invoicing_id.recurring_next_date, service_invoicing_id.contract_line_ids[0].recurring_next_date)
        self.assertEqual(service_invoicing_id.recurring_interval, service_invoicing_id.contract_line_ids[0].recurring_interval)
        self.assertEqual(service_invoicing_id.recurring_rule_type, service_invoicing_id.contract_line_ids[0].recurring_rule_type)
        self.assertEqual(service_invoicing_id.recurring_invoicing_type, service_invoicing_id.contract_line_ids[0].recurring_invoicing_type)