import datetime
import logging
import re
from collections import namedtuple

from odoo import models
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities.utils import contract_utils

_logger = logging.getLogger(__name__)


class ActionCreate(models.AbstractModel):
    _name = "energy_communities_service_invoicing.action_create"

    def get_product_pack(self, selfconsumption_project):
        PackTuple = namedtuple("PackTuple", "pack,product_template")
        pack_dict = {
            "power_acquired": PackTuple(
                pack=self.env.ref(
                    "energy_selfconsumption.product_product_power_acquired_product_pack_template"
                ),
                product_template=self.env.ref(
                    "energy_selfconsumption.product_product_power_acquired_product_template"
                ),
            ),
            "energy_delivered": PackTuple(
                pack=self.env.ref(
                    "energy_selfconsumption.product_product_energy_delivered_product_pack_template"
                ),
                product_template=self.env.ref(
                    "energy_selfconsumption.product_product_energy_delivered_product_template"
                ),
            ),
            "energy_custom": PackTuple(
                pack=self.env.ref(
                    "energy_selfconsumption.product_product_energy_custom_product_pack_template"
                ),
                product_template=self.env.ref(
                    "energy_selfconsumption.product_product_energy_custom_product_template"
                ),
            ),
        }
        pack_tuple = pack_dict.get(selfconsumption_project.invoicing_mode, None)
        if not pack_tuple:
            raise ValidationError(_("Invalid invoicing mode"))
        return pack_tuple.pack, pack_tuple.product_template

    def get_pricelist_for_project(self, selfconsumption_project, price):
        _, product_template = self.get_product_pack(selfconsumption_project)
        # Create pricelist
        pricelist = self.env["product.pricelist"].create(
            {
                "name": f"{selfconsumption_project.name} Pricelist",
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

    def update_selfconsumption_project(self, selfconsumption_project, contracts):
        price = contracts[0].contract_line_ids[0].price_unit
        pack, _ = self.get_product_pack(selfconsumption_project)
        pricelist = self.get_pricelist_for_project(selfconsumption_project, price)
        payment_mode = contracts[0].payment_mode_id

        selfconsumption_project.write(
            {
                "product_id": pack.product_variant_id.id,
                "recurring_rule_type": contracts[0].recurring_rule_type,
                "recurring_interval": contracts[0].recurring_interval,
                "recurring_invoicing_type": contracts[0].recurring_invoicing_type,
                "pricelist_id": pricelist.id,
                "payment_mode_id": payment_mode.id,
            }
        )

    def get_supply_point_id(self, selfconsumption_project, contract):
        contract_cups = contract.contract_line_ids[0].name
        match = re.search(r"CUPS:\s*(\S+)", contract_cups)
        if match:
            contract_cups = match.group(1)
            supply_point_id = self.env["energy_selfconsumption.supply_point"].search(
                [("code", "=", contract_cups)]
            )
            if not supply_point_id:
                raise ValidationError(
                    _(
                        "Supply point not found. Company: %s, Proyect: %s, Contract: %s, Line: %s",
                        contract.company_id.name,
                        selfconsumption_project.name,
                        contract.name,
                        contract_cups,
                    )
                )
            if len(supply_point_id) > 1:
                raise ValidationError(
                    _(
                        "More than one supply point found. Company: %s, Proyect: %s, Contract: %s, Line: %s",
                        contract.company_id.name,
                        selfconsumption_project.name,
                        contract.name,
                        contract_cups,
                    )
                )
        else:
            raise ValidationError(
                _(
                    "CUPS not found in contract line description. Company: %s, Proyect: %s, Contract: %s, Line: %s",
                    contract.company_id.name,
                    selfconsumption_project.name,
                    contract.name,
                    contract_cups,
                )
            )
        return supply_point_id

    def reclose_contract(self, contract):
        assert (
            bool(contract.date_end) is True
        ), f"Contract {contract.name} has not date_end definded"
        with contract_utils(self.env, contract) as component:
            component.set_contract_status_closed(contract.date_end)

    def reopen_contract_without_date_end(self, selfconsumption_project, contract):
        assert (
            contract.date_end is False
        ), f"Contract {contract.name} has already an end date"

        price = contract.contract_line_ids[0].price_unit
        pack, _ = self.get_product_pack(selfconsumption_project)
        pricelist = selfconsumption_project.pricelist_id
        payment_mode = selfconsumption_project.payment_mode_id
        supply_point_id = self.get_supply_point_id(selfconsumption_project, contract)
        contract._compute_recurring_next_date()
        execute_date = (
            contract.last_date_invoiced
            if contract.last_date_invoiced
            else contract.date_start
        )
        with contract_utils(self.env, contract) as component:
            component.set_contract_status_closed(execute_date)
            if contract.recurring_rule_type == "monthlylastday":
                execute_date = execute_date + datetime.timedelta(days=1)
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
                    "journal_id": contract.journal_id.id,
                    "project_id": selfconsumption_project.id,
                    "company_id": selfconsumption_project.company_id.id,
                },
            )
        with contract_utils(self.env, new_contract_id) as component:
            component.set_contract_status_active(execute_date)
        return new_contract_id

    def setup_contract_line_description(self, project, contract_id):
        distribution_table_active = project.distribution_table_ids.filtered(
            lambda table: table.state == "active"
        )
        project._setup_selfconsumption_contract_line_description(
            distribution_table_active, contract_id
        )

    def setup_contract_main_line(self, contract_id):
        contract_id.contract_line_ids[0].write({"main_line": True})

    def update_old_contract_to_service_invoicing(self):
        migrated_contracts = []
        _logger.info("Starting update_old_contract_to_service_invoicing.")

        selfconsumption_project_ids = self.env[
            "energy_selfconsumption.selfconsumption"
        ].search([("state", "=", "active"), ("company_id", "!=", 29)])

        for project in selfconsumption_project_ids:
            sale_orders = project.get_sale_orders()
            contracts = project.get_contracts()
            project_for_update = len(sale_orders) == 0 and len(contracts) > 0

            if (
                project_for_update
            ):  # if there are no sale orders, we need to reopen the contracts
                _logger.info(
                    f"Reopening contracts for selfconsumption project {project.name}."
                )
                _logger.info(f"Update Selfconsumption project {project.name}.")
                self.update_selfconsumption_project(project, contracts)
                _logger.info(f"Selfconsumption {project.name} updated.")

                for contract in contracts:
                    _logger.info(f"Reopening contract {contract.name}.")
                    if contract.date_end:
                        self.reclose_contract(contract)
                        migrated_contracts.append(contract)
                    else:
                        contract_id = self.reopen_contract_without_date_end(
                            project, contract
                        )
                        _logger.info("Setup contract line description.")
                        self.setup_contract_line_description(project, contract_id)

                        _logger.info("Setup contract line main_line.")
                        self.setup_contract_main_line(contract_id)
                        migrated_contracts.append(contract_id)
                        _logger.info(f"Contract {contract_id.name} reopened.")
        return migrated_contracts

    def update_supply_point_assignation_on_selfconsumption_contracts(self):
        migrated_contracts = []
        _logger.info("Starting update_old_contract_to_service_invoicing.")

        selfconsumption_project_ids = self.env[
            "energy_selfconsumption.selfconsumption"
        ].search([("state", "=", "active"), ("company_id", "!=", 29)])

        for selfconsumption in selfconsumption_project_ids:
            contracts = self.env["contract.contract"].search(
                [
                    ("project_id", "=", selfconsumption.project_id.id),
                    ("predecessor_contract_id", "!=", False),
                ]
            )
            for contract in contracts:
                contract.write(
                    {
                        "supply_point_assignation_id": contract.predecessor_contract_id.supply_point_assignation_id.id
                    }
                )
                if selfconsumption.invoicing_mode == "energy_delivered":
                    for line in contract.contract_line_ids:
                        line.write(
                            {
                                "qty_formula_id": self.env.ref(
                                    "energy_selfconsumption.energy_delivered_formula"
                                ).id
                            }
                        )
                self.env["sale.order.metadata.line"].create(
                    {
                        "order_id": contract.sale_order_id.id,
                        "key": "supply_point_assignation_id",
                        "value": str(
                            contract.predecessor_contract_id.supply_point_assignation_id.id
                        ),
                    }
                )
                self.setup_contract_line_description(selfconsumption, contract)

    _logger.info("Everything went good!")
