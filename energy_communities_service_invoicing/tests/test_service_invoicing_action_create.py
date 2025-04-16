import unittest

from dateutil.relativedelta import relativedelta

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)


@tagged("-at_install", "post_install")
class TestActionCreate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.ActionCreate = self.env[
            "energy_communities_service_invoicing.action_create"
        ]
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

    def test_update_selfconsumption_project(self):
        # Given a project
        selfconsumption_project = self.env[
            "energy_selfconsumption.selfconsumption"
        ].search([("id", "=", 29)])
        # and a set of contracts
        contracts = selfconsumption_project.get_contracts()

        # when we update that project and contracts
        res = self.ActionCreate.update_selfconsumption_project(
            selfconsumption_project, contracts
        )

        # then no errors happend
        self.assertIsNone(res)

    def test_reclose_contract__ok(self):
        # given a contract that has already a date_end
        contract = self.env["contract.contract"].search([("id", "=", 66)])[0]
        # a close_date
        close_date = contract.date_end
        # when we reclose that contract
        self.ActionCreate.reclose_contract(contract)

        # then
        self.assertEqual(contract.contract_line_ids[0].date_end, close_date)
        self.assertEqual(contract.date_end, close_date)
        self.assertEqual(contract.status, "closed")
        self.assertFalse(bool(contract.recurring_next_date))

    @unittest.skip("Find a contract without date_end to test")
    def test_reopen_contract_without_date_end__ok(self):
        # Given a project
        selfconsumption_project = self.env[
            "energy_selfconsumption.selfconsumption"
        ].search([("id", "=", 29)])
        # with a contract that has already a date_end
        contract = None  # self.env["contract.contract"].search([("id", "=", 66)])[0]

        # when we reopen that contract
        self.ActionCreate.reopen_contract_without_date_end(
            selfconsumption_project, contract
        )

        # then
        self.assertTrue(bool(contract.recurring_next_date))
        self.assertTrue(bool(new_contract_id.recurring_next_date))

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
