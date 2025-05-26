from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)


@tagged("-at_install", "post_install")
class TestServiceInvoicingComponents(TransactionCase):
    # TODO: Test configuration journal correctly defined
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_service_invoicing_wizard_creation_ok(self):
        # given a service invoicing contract created from wizard
        creation_wizard = self._get_service_invoicing_creation_wizard()
        contract_view = creation_wizard.execute_create()
        contract = self.env["contract.contract"].browse(int(contract_view["res_id"]))
        # the contract is defined based on wizard values
        self.assertTrue(bool(contract))
        self.assertEqual(contract.status, "paused")
        self.assertEqual(contract.date_start, creation_wizard.execution_date)
        self.assertEqual(contract.partner_id, creation_wizard.company_id.partner_id)
        self.assertEqual(
            contract.community_company_id, creation_wizard.community_company_id
        )
        self.assertEqual(contract.pricelist_id, creation_wizard.pricelist_id)
        self.assertEqual(contract.payment_mode_id, creation_wizard.payment_mode_id)
        self.assertEqual(contract.discount, creation_wizard.discount)
        self.assertEqual(contract.recurring_next_date, creation_wizard.execution_date)

    def test_close_contract_ok(self):
        # given a service invoicing contract created from wizard
        contract = self._get_wizard_service_invoicing_contract()
        initial_recurring_next_date = contract.recurring_next_date
        self.assertEqual(contract.date_start, initial_recurring_next_date)
        contract_date = contract.date_start
        with contract_utils(self.env, contract) as component:
            component.set_contract_status_closed(contract_date)
        self.assertEqual(contract.status, "closed")
        self.assertEqual(contract.date_end, contract_date)
        self.assertEqual(contract.recurring_next_date, contract_date)

    def test_service_invoicing_recurrency(self):
        contract = self._get_component_service_invoicing_contract(
            recurring_rule_type="monthly",
            recurring_interval=1,
            recurring_invoicing_type="pre-paid",
        )
        self.assertEqual(contract.recurring_next_date, contract.date_start)
        contract = self._get_component_service_invoicing_contract(
            recurring_rule_type="monthly",
            recurring_interval=1,
            recurring_invoicing_type="post-paid",
        )
        self.assertEqual(
            contract.recurring_next_date, contract.date_start + relativedelta(months=+1)
        )
        contract = self._get_component_service_invoicing_contract(
            recurring_rule_type="monthlylastday",
            recurring_interval=1,
            recurring_invoicing_type="post-paid",
        )
        self.assertEqual(
            contract.recurring_next_date, contract.date_start + relativedelta(day=31)
        )
        contract = self._get_component_service_invoicing_contract(
            recurring_rule_type="monthlylastday",
            recurring_interval=2,
            recurring_invoicing_type="post-paid",
        )
        self.assertEqual(
            contract.recurring_next_date,
            contract.date_start + relativedelta(months=+1) + relativedelta(day=31),
        )

    def test_service_invoicing_reopen_recurrency(self):
        self._reopen_workflow_test("monthly", 1, "pre-paid")
        self._reopen_workflow_test("monthlylastday", 2, "pre-paid")
        self._reopen_workflow_test("monthlylastday", 2, "post-paid")
        self._reopen_workflow_test("monthly", 2, "post-paid")

    def test_service_invoicing_modification_recurrency(self):
        self._modification_workflow_test("monthly", 1, "pre-paid")
        self._modification_workflow_test("monthlylastday", 2, "pre-paid")
        self._modification_workflow_test("monthlylastday", 2, "post-paid")
        self._modification_workflow_test("monthly", 2, "post-paid")

    def _reopen_workflow_test(
        self, recurring_rule_type, recurring_interval, recurring_invoicing_type
    ):
        contract = self._get_component_service_invoicing_contract(
            recurring_rule_type=recurring_rule_type,
            recurring_interval=recurring_interval,
            recurring_invoicing_type=recurring_invoicing_type,
        )
        with contract_utils(self.env, contract) as component:
            component.work.record.recurring_create_invoice()
            initial_recurring_next_date = contract.recurring_next_date
            component.set_contract_status_closed(
                component.work.record.last_date_invoiced
            )
            reopen_date = component.work.record.last_date_invoiced + relativedelta(
                days=+1
            )
            new_contract = component.reopen(
                reopen_date,
                component.work.record.pricelist_id,
                component.work.record.pack_id,
            )
        self.assertEqual(contract.recurring_rule_type, new_contract.recurring_rule_type)
        self.assertEqual(contract.recurring_interval, new_contract.recurring_interval)
        self.assertEqual(
            contract.recurring_invoicing_type, new_contract.recurring_invoicing_type
        )
        self.assertEqual(initial_recurring_next_date, new_contract.recurring_next_date)

    def _modification_workflow_test(
        self, recurring_rule_type, recurring_interval, recurring_invoicing_type
    ):
        contract = self._get_component_service_invoicing_contract(
            recurring_rule_type=recurring_rule_type,
            recurring_interval=recurring_interval,
            recurring_invoicing_type=recurring_invoicing_type,
        )
        with contract_utils(self.env, contract) as component:
            component.work.record.recurring_create_invoice()
            initial_recurring_next_date = contract.recurring_next_date
            modification_date = (
                component.work.record.last_date_invoiced + relativedelta(days=+1)
            )
            new_contract = component.modify(
                modification_date,
                "modify_discount",
                pricelist_id=None,
                pack_id=None,
                discount=12,
                payment_mode_id=None,
            )
        self.assertEqual(contract.recurring_rule_type, new_contract.recurring_rule_type)
        self.assertEqual(contract.recurring_interval, new_contract.recurring_interval)
        self.assertEqual(
            contract.recurring_invoicing_type, new_contract.recurring_invoicing_type
        )
        self.assertEqual(initial_recurring_next_date, new_contract.recurring_next_date)

    def _get_service_invoicing_creation_wizard(self):
        return self.env["service.invoicing.action.create.wizard"].create(
            {
                "execution_date": datetime.now(),
                "company_id": self.env.ref(
                    "energy_communities.coordinator_company_1"
                ).id,
                "community_company_id": self._get_community_1_company().id,
                "platform_pack_id": self.env.ref(
                    "energy_communities_service_invoicing.demo_platform_pack_product_template"
                ).product_variant_id.id,
                "pricelist_id": self.env.ref(
                    "energy_communities_service_invoicing.demo_service_invoicing_pricelist"
                ).id,
                "payment_mode_id": self.env.ref(
                    "account_payment_mode.payment_mode_inbound_dd1"
                ).id,
                "discount": 15,
            }
        )

    def _get_wizard_service_invoicing_contract(self):
        creation_wizard = self._get_service_invoicing_creation_wizard()
        contract_view = creation_wizard.execute_create()
        return self.env["contract.contract"].browse(int(contract_view["res_id"]))

    def _get_component_service_invoicing_contract(
        self,
        recurring_rule_type=False,
        recurring_interval=False,
        recurring_invoicing_type=False,
    ):
        so_metadata = {
            "company_id": self.env.ref("energy_communities.coordinator_company_1").id,
            "pricelist_id": self.env.ref(
                "energy_communities_service_invoicing.demo_service_invoicing_pricelist"
            ).id,
        }
        if recurring_rule_type:
            so_metadata["recurring_rule_type"] = recurring_rule_type
        if recurring_interval:
            so_metadata["recurring_interval"] = recurring_interval
        if recurring_invoicing_type:
            so_metadata["recurring_invoicing_type"] = recurring_invoicing_type
        # create service invoicing
        with sale_order_utils(self.env) as component:
            contract = component.create_service_invoicing_initial(
                self._get_community_1_company().partner_id,
                self.env.ref(
                    "energy_communities_service_invoicing.demo_platform_pack_product_template"
                ),
                self.env.ref(
                    "energy_communities_service_invoicing.demo_service_invoicing_pricelist"
                ),
                fields.Date.today(),
                "activate",
                "testing_contract",
                False,  # TODO: no payment mode defined!
                so_metadata,
            )
        with contract_utils(self.env, contract) as component:
            component.set_contract_status_active(component.work.record.date_start)
        return contract

    def _get_community_1_company(self):
        return self.env["res.company"].search([("name", "=", "Community 1")], limit=1)
