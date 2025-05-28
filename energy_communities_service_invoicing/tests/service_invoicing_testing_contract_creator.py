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
