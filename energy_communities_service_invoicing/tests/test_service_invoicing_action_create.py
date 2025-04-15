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

    def _get_pricelist_for_contract(self, contract, selfconsumption_project):
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
        return pricelist

    def _get_payment_mode(self, selfconsumption_project):
        return self.env["account.payment.mode"].search(
            [
                ("company_id", "=", selfconsumption_project.company_id.id),
                ("payment_type", "=", "inbound"),
            ]
        )

    def _get_journal(self, selfconsumption_project):
        return self.env["account.journal"].search(
            [
                ("company_id", "=", selfconsumption_project.company_id.id),
                ("type", "=", "sale"),
            ],
            limit=1,
        )

    def _get_supply_point(self, contract):
        supply_point_id = None
        contract_cups = contract.contract_line_ids[0].name
        match = re.search(r"CUPS:\s*(\S+)", contract_cups)
        if match:
            contract_cups = match.group(1)
            supply_point_id = self.env["energy_selfconsumption.supply_point"].search(
                [("code", "=", contract_cups)]
            )
        return supply_point_id

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

    # @unittest.skip("skip")
    def test_contract_recurrency_ok(self):
        # Given a project with one contract
        selfconsumption_project = self.env[
            "energy_selfconsumption.selfconsumption"
        ].search([("id", "=", 29)])
        contract = self.env["contract.contract"].search([("id", "=", 66)])[0]
        # and a pricelist
        pricelist = self._get_pricelist_for_contract(contract, selfconsumption_project)
        # and a product pack
        pack = self.env.ref(
            "energy_selfconsumption.product_product_energy_delivered_product_pack_template"
        )
        # and a payment mode
        payment_mode = self._get_payment_mode(selfconsumption_project)
        # and a journal_id
        journal_id = self._get_journal(selfconsumption_project)
        # and a supply_point
        supply_point_id = self._get_supply_point(contract)

        with contract_utils(self.env, contract) as component:
            if contract.date_end:
                close_date = contract.date_end
                # TODO: Verify why not all lines preserve date_end after this execution
                # __import__('ipdb').set_trace()
                component.set_contract_status_closed(close_date)
                # __import__('ipdb').set_trace()
                self.assertEqual(contract.contract_line_ids[0].date_end, close_date)
                self.assertEqual(contract.date_end, close_date)
                self.assertEqual(contract.status, "closed")
                self.assertFalse(bool(contract.recurring_next_date))
            else:
                execute_date = (
                    contract.last_date_invoiced
                    if contract.last_date_invoiced
                    else contract.date_start
                )
                component.set_contract_status_closed(execute_date)
                new_contract_id = component.reopen(
                    execute_date,
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
                self.assertTrue(bool(new_contract_id.recurring_next_date))

                with contract_utils(self.env, service_invoicing_id) as component:
                    component.set_contract_status_active(contract.last_date_invoiced)

                # Then
                self.assertEqual(new_contract_id.status, "in_progress")
                self.assertEqual(new_contract_id.date_start, execution_date)
                self.assertEqual(contract.date_end, contract.last_date_invoiced)
        # self.assertEqual(
        #     service_invoicing_id.recurring_next_date,
        #     contract.recurring_next_date
        # )
        # self.assertEqual(
        #     service_invoicing_id.contract_line_ids[0].recurring_next_date,
        #     contract.contract_line_ids[0].recurring_next_date
        # )
        # self.assertEqual(
        #     service_invoicing_id.recurring_next_date,
        #     service_invoicing_id.contract_line_ids[0].recurring_next_date
        # )
        # self.assertEqual(
        #     service_invoicing_id.recurring_interval,
        #     service_invoicing_id.contract_line_ids[0].recurring_interval
        # )
        # self.assertEqual(
        #     service_invoicing_id.recurring_rule_type,
        #     service_invoicing_id.contract_line_ids[0].recurring_rule_type
        # )
        # self.assertEqual(
        #     service_invoicing_id.recurring_invoicing_type,
        #     service_invoicing_id.contract_line_ids[0].recurring_invoicing_type
        # )

    @unittest.skip("skip")
    def test_pass_service_invoicing_migration(self):
        self.env[
            "energy_selfconsumption.selfconsumption"
        ].update_old_contract_to_service_invoicing()
        contracts = self.env["contract.contract"].search(
            [("predecessor_contract_id", "!=", False)]
        )
        for contract in contracts:
            predecessor_contract = contract.predecessor_contract_id
            self.assertEqual(contract.status, "in_progress")
            # Check consistency between contract and predecessor_contract
            self.assertEqual(
                contract.date_start, predecessor_contract.last_date_invoiced
            )
            if predecessor_contract.last_date_invoiced:
                self.assertEqual(
                    predecessor_contract.date_end,
                    predecessor_contract.last_date_invoiced,
                )
                self.assertEqual(
                    contract.recurring_next_date,
                    predecessor_contract.recurring_next_date,
                )
            else:  # If there is no last_date_invoiced, means the contract has not invoiced so we close the same day it started
                self.assertEqual(
                    predecessor_contract.date_end, predecessor_contract.date_start
                )
                self.assertTrue(bool(contract.recurring_next_date))
                self.assertFalse(predecessor_contract.recurring_next_date)
            self.assertEqual(
                contract.contract_line_ids[0].recurring_next_date,
                predecessor_contract.contract_line_ids[0].recurring_next_date,
            )
            # Check consintensy between contract and contract_line
            self.assertEqual(
                contract.recurring_next_date,
                contract.contract_line_ids[0].recurring_next_date,
            )
            self.assertEqual(
                contract.recurring_interval,
                contract.contract_line_ids[0].recurring_interval,
            )
            self.assertEqual(
                contract.recurring_rule_type,
                contract.contract_line_ids[0].recurring_rule_type,
            )
            self.assertEqual(
                contract.recurring_invoicing_type,
                contract.contract_line_ids[0].recurring_invoicing_type,
            )
