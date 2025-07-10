from datetime import datetime

from odoo import fields

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)


class ServiceInvoicingTestingContractCreator:
    _name = "energy_communities_service_invoicing.service_invoicing_testing_contract_creator"

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
                "pricelist_id": self.env.ref("product.list0").id,
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
        self, so_metadata=False, execution_date=False
    ):
        if not so_metadata:
            so_metadata = {}
        if not execution_date:
            execution_date = fields.Date.today()
        so_metadata = so_metadata | {
            "company_id": self.env.ref("energy_communities.coordinator_company_1").id,
            "pricelist_id": self.env.ref("product.list0").id,
        }
        # create service invoicing
        with sale_order_utils(self.env) as component:
            contract = component.create_service_invoicing_initial(
                self._get_community_1_company().partner_id,
                self.env.ref(
                    "energy_communities_service_invoicing.demo_platform_pack_product_template"
                ),
                self.env.ref("product.list0"),
                execution_date,
                "activate",
                "testing_contract",
                False,  # TODO: no payment mode defined!
                so_metadata,
            )
        with contract_utils(self.env, contract) as component:
            component.activate(component.work.record.date_start)
        return contract

    def _get_community_1_company(self):
        return self.env["res.company"].search([("name", "=", "Community 1")], limit=1)

    def _assert_recurrency_config_consistency_between_old_and_new(
        self,
        old_contract,
        new_contract,
        initial_recurring_next_date,
        initial_next_period_date_start,
        initial_next_period_date_end,
    ):
        new_contract_line = new_contract.contract_line_ids[0]
        # on lines
        self.assertEqual(
            initial_recurring_next_date, new_contract_line.recurring_next_date
        )
        self.assertEqual(
            initial_next_period_date_start, new_contract_line.next_period_date_start
        )
        self.assertEqual(
            initial_next_period_date_end, new_contract_line.next_period_date_end
        )
        self.assertEqual(
            old_contract.recurring_rule_type, new_contract_line.recurring_rule_type
        )
        self.assertEqual(
            old_contract.recurring_interval, new_contract_line.recurring_interval
        )
        self.assertEqual(
            old_contract.recurring_invoicing_type,
            new_contract_line.recurring_invoicing_type,
        )
        self.assertEqual(
            old_contract.recurring_rule_mode, new_contract_line.recurring_rule_mode
        )
        self.assertEqual(
            old_contract.recurring_invoicing_fixed_type,
            new_contract_line.recurring_invoicing_fixed_type,
        )
        self.assertEqual(
            old_contract.fixed_invoicing_day, new_contract_line.fixed_invoicing_day
        )
        self.assertEqual(
            old_contract.fixed_invoicing_month, new_contract_line.fixed_invoicing_month
        )
        # on contract
        self.assertEqual(old_contract.journal_id, new_contract.journal_id)
        self.assertEqual(initial_recurring_next_date, new_contract.recurring_next_date)
        self.assertEqual(
            initial_next_period_date_start, new_contract.next_period_date_start
        )
        self.assertEqual(
            initial_next_period_date_end, new_contract.next_period_date_end
        )
        self.assertEqual(
            old_contract.recurring_rule_type, new_contract.recurring_rule_type
        )
        self.assertEqual(
            old_contract.recurring_interval, new_contract.recurring_interval
        )
        self.assertEqual(
            old_contract.recurring_invoicing_type, new_contract.recurring_invoicing_type
        )
        self.assertEqual(
            old_contract.recurring_rule_mode, new_contract.recurring_rule_mode
        )
        self.assertEqual(
            old_contract.recurring_invoicing_fixed_type,
            new_contract.recurring_invoicing_fixed_type,
        )
        self.assertEqual(
            old_contract.fixed_invoicing_day, new_contract.fixed_invoicing_day
        )
        self.assertEqual(
            old_contract.fixed_invoicing_month, new_contract.fixed_invoicing_month
        )
