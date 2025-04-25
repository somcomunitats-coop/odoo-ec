import datetime
import logging
import unittest

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)

_logger = logging.getLogger(__name__)


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
        self._check_contract_closing_params(contract, close_date)

    # TODO: See how we could assert this
    @unittest.skip("skip")
    def test_reclose_contract_without_date_end__fails(self):
        # given a contract that has already a date_end
        contract = self.env["contract.contract"].search([("id", "=", 13)])[0]
        # a close_date
        close_date = contract.date_end
        try:
            # when we reclose that contract
            self.ActionCreate.reclose_contract(contract)
        except Exception:
            # then
            pass
            # self.assertIsInstance(Exception,AssertionError)

    def test_existing_open_contracts_without_recurring_have_no_invoices(self):
        contracts = self.env["contract.contract"].search([])
        self.assertTrue(bool(contracts))
        for contract in contracts:
            if not contract.last_date_invoiced:
                self.assertFalse(bool(contract._get_related_invoices()))

    def test_reopen_contract_without_date_end__ok(self):
        # Given a project
        selfconsumption_project = self.env[
            "energy_selfconsumption.selfconsumption"
        ].search([("id", "=", 25)])
        # with a contract without date_end
        contracts = selfconsumption_project.get_contracts()
        # when we update that project and contracts
        res = self.ActionCreate.update_selfconsumption_project(
            selfconsumption_project, contracts
        )
        contract = self.env["contract.contract"].search([("id", "=", 13)])[0]
        # contract = self.env["contract.contract"].search([("id", "=", 67)])[0]
        initial_recurring_next_date = {contract.id: contract.recurring_next_date}
        # when we reopen that contract
        new_contract_id = self.ActionCreate.reopen_contract_without_date_end(
            selfconsumption_project, contract
        )
        # then
        self._check_contract_creation_params(
            contract, new_contract_id, initial_recurring_next_date
        )
        self._check_project_contract_params_consistency(new_contract_id)

    # TODO: See how we could assert this
    @unittest.skip("skip")
    def test_reopen_contract_with_date_end__fails(self):
        # Given a project
        selfconsumption_project = self.env[
            "energy_selfconsumption.selfconsumption"
        ].search([("id", "=", 29)])
        # with a contract without date_end
        contract = self.env["contract.contract"].search([("id", "=", 66)])[0]
        initial_recurring_next_date = {contract.id: contract.recurring_next_date}
        try:
            # when we reopen that contract
            new_contract_id = self.ActionCreate.reopen_contract_without_date_end(
                selfconsumption_project, contract
            )
        except Exception as e:
            pass

    def test_pass_service_invoicing_migration(self):
        contracts = self.env["contract.contract"].search([])
        recurring_next_dates = {}
        closing_dates = {}
        for contract in contracts:
            contract._compute_recurring_next_date()
            recurring_next_dates[contract.id] = contract.recurring_next_date
            closing_dates[contract.id] = contract.date_end
        migrated_contracts = (
            self.ActionCreate.update_old_contract_to_service_invoicing()
        )
        for contract in migrated_contracts:
            if contract.predecessor_contract_id:
                self._check_contract_creation_params(
                    contract.predecessor_contract_id, contract, recurring_next_dates
                )
                if contract.recurring_rule_type == "monthlylastday":
                    close_date = contract.date_start - datetime.timedelta(days=1)
                else:
                    close_date = contract.date_start
                self._check_contract_closing_params(
                    contract.predecessor_contract_id, close_date
                )
                # Check main line
                self.assertTrue(contract.contract_line_ids[0].main_line)
                # Check consistency between contract and project params
                self._check_project_contract_params_consistency(contract)
            else:
                self._check_contract_closing_params(
                    contract, closing_dates[contract.id]
                )

    def _check_project_contract_params_consistency(self, contract):
        _logger.info(
            "Checking project and contract params consistency for contract {}.".format(
                contract.name
            )
        )
        selfconsumption_project = self.env[
            "energy_selfconsumption.selfconsumption"
        ].search([("project_id", "=", contract.project_id.id)], limit=1)
        # check journal
        self.assertTrue(bool(contract.journal_id))
        self.assertEqual(
            contract.journal_id.id, contract.predecessor_contract_id.journal_id.id
        )
        # check product
        self.assertTrue(bool(selfconsumption_project.product_id))
        self.assertEqual(
            contract.contract_template_id.contract_line_ids[0].product_id,
            selfconsumption_project.product_id.property_contract_template_id.contract_line_ids[
                0
            ].product_id,
        )
        self.assertEqual(
            contract.contract_template_id,
            selfconsumption_project.product_id.property_contract_template_id,
        )
        # check pricelist
        self.assertEqual(contract.pricelist_id, selfconsumption_project.pricelist_id)
        # check recurrency
        self.assertEqual(
            contract.recurring_rule_type, selfconsumption_project.recurring_rule_type
        )
        self.assertEqual(
            contract.recurring_rule_type,
            contract.predecessor_contract_id.recurring_rule_type,
        )
        self.assertEqual(
            contract.recurring_interval, selfconsumption_project.recurring_interval
        )
        self.assertEqual(
            contract.recurring_interval,
            contract.predecessor_contract_id.recurring_interval,
        )
        self.assertEqual(
            contract.recurring_invoicing_type,
            selfconsumption_project.recurring_invoicing_type,
        )
        self.assertEqual(
            contract.recurring_invoicing_type,
            contract.predecessor_contract_id.recurring_invoicing_type,
        )
        # check payment_mode
        self.assertEqual(
            contract.payment_mode_id, selfconsumption_project.payment_mode_id
        )
        self.assertEqual(
            contract.payment_mode_id, contract.predecessor_contract_id.payment_mode_id
        )

    def _check_contract_closing_params(self, contract, close_date):
        _logger.info("Checking closing params for contract {}.".format(contract.name))

        self.assertEqual(contract.contract_line_ids[0].date_end, close_date)
        self.assertEqual(contract.date_end, close_date)
        self.assertEqual(contract.status, "closed")

    def _check_contract_creation_params(
        self, contract, new_contract_id, recurring_next_dates
    ):
        _logger.info("Checking creation params for contract {}.".format(contract.name))

        self.assertIn(contract.status, ["closed", "closed_planned"])
        self.assertEqual(new_contract_id.status, "in_progress")
        # we preserve data between old and new contract
        self.assertEqual(
            new_contract_id.recurring_interval, contract.recurring_interval
        )
        self.assertEqual(
            new_contract_id.recurring_rule_type, contract.recurring_rule_type
        )
        self.assertEqual(
            new_contract_id.recurring_invoicing_type, contract.recurring_invoicing_type
        )
        self.assertTrue(bool(new_contract_id.recurring_next_date))
        self.assertEqual(
            new_contract_id.recurring_next_date, recurring_next_dates[contract.id]
        )

        if contract.last_date_invoiced:
            date_check = contract.last_date_invoiced
        else:
            date_check = contract.date_start
        if new_contract_id.recurring_rule_type == "monthlylastday":
            date_check = date_check + datetime.timedelta(days=1)
        self.assertEqual(new_contract_id.date_start, date_check)

        # we have consistency between new contract and it's lines
        self.assertEqual(
            new_contract_id.recurring_next_date,
            new_contract_id.contract_line_ids[0].recurring_next_date,
        )
        self.assertEqual(
            new_contract_id.recurring_interval,
            new_contract_id.contract_line_ids[0].recurring_interval,
        )
        self.assertEqual(
            new_contract_id.recurring_rule_type,
            new_contract_id.contract_line_ids[0].recurring_rule_type,
        )
        self.assertEqual(
            new_contract_id.recurring_invoicing_type,
            new_contract_id.contract_line_ids[0].recurring_invoicing_type,
        )
