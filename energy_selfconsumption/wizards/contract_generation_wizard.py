from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)


class ContractGenerationWizard(models.TransientModel):
    _name = "energy_selfconsumption.contract_generation.wizard"
    _description = "Service to generate contract"

    selfconsumption_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption", readonly=True
    )
    start_date = fields.Date(
        string="Start date",
        help="Starting date of the invoicing",
        required=True,
        default=fields.Date.today(),
    )
    payment_mode = fields.Many2one(
        "account.payment.mode",
        string="Payment mode",
        default=lambda self: self._default_payment_mode(),
    )

    def _default_payment_mode(self):
        return self.env["account.payment.mode"].search(
            [("company_id", "=", self.env.company.id), ("payment_type", "=", "inbound")]
        )

    def _get_impacted_sale_orders(self):
        sale_orders = self.selfconsumption_id.get_sale_orders()
        return sale_orders.filtered(lambda so: so.state == "draft")

    def action_generate_contracts(self):
        # Get distribution table
        distribution_id = (
            self.selfconsumption_id.distribution_table_ids.filtered_domain(
                [("state", "=", "process")]
            )
        )
        if not distribution_id:
            raise ValidationError(
                _("There is no distribution table in proces of activation.")
            )
        # Iterate trough sale orders and:
        for sale_order in self._get_impacted_sale_orders():
            # 1.-confirm sale order
            so_extra = {
                "commitment_date": self.start_date,
                "payment_mode_id": self.payment_mode.id,
            }
            with sale_order_utils(self.env, sale_order) as component:
                contract = component.confirm(**so_extra)
            # 2.- setup contract line description
            # TODO: This must be moved to contract dynamic invoice generation
            self._setup_selfconsumption_contract_line_description(
                distribution_id, contract, sale_order
            )
            # 3.- setup contract line main_line
            contract.contract_line_ids[0].write({"main_line": True})
            # 4.- mark contract as active
            with contract_utils(self.env, contract) as component:
                component.set_contract_status_active(self.start_date)
        # 5.- mark project as active
        self.selfconsumption_id.write({"state": "active"})
        #  6.- mark distribution table as active
        self.selfconsumption_id.distribution_table_state("process", "active")
        return True

    # TODO: This must be moved to contract dynamic invoice generation
    def _setup_selfconsumption_contract_line_description(
        self, distribution_id, contract, sale_order
    ):
        for contract_line in contract.contract_line_ids:
            supply_point_assignation = (
                distribution_id.supply_point_assignation_ids.filtered_domain(
                    [
                        (
                            "supply_point_id",
                            "=",
                            int(
                                sale_order.metadata_line_ids.filtered_domain(
                                    [("key", "=", "supply_point_id")]
                                ).mapped("value")[0]
                            ),
                        ),
                    ]
                )
            )
            data = {
                "code": supply_point_assignation.supply_point_id.code,
                "owner_id": supply_point_assignation.supply_point_id.owner_id.display_name,
                "cau": self.selfconsumption_id.code,
            }
            contract_line.name.replace("#code#", data["code"])
            contract_line.name.replace("#owner_id#", data["owner_id"])
            # Each invoicing type has different data in the description column, so we need to check and modify
            if self.selfconsumption_id.invoicing_mode == "energy_delivered":
                contract_line.name.replace("#cau#", data["cau"])
            elif self.selfconsumption_id.invoicing_mode == "power_acquired":
                data["power"] = self.selfconsumption_id.power
                data["coefficient"] = supply_point_assignation.coefficient
                (
                    first_date_invoiced,
                    last_date_invoiced,
                    recurring_next_date,
                ) = contract_line._get_period_to_invoice(
                    contract_line.last_date_invoiced,
                    contract_line.recurring_next_date,
                )
                data["days_invoiced"] = (
                    (last_date_invoiced - first_date_invoiced).days + 1
                    if first_date_invoiced and last_date_invoiced
                    else 0
                )
                data["power_acquired"] = (
                    round(
                        self.selfconsumption_id.power
                        * supply_point_assignation.coefficient,
                        2,
                    )
                    if supply_point_assignation.coefficient
                    else 0.0
                )
                data["total_amount"] = round(
                    data["days_invoiced"] * data["power_acquired"], 2
                )
                contract_line.name.replace("#cau#", data["cau"])
                contract_line.name.replace("#power#", str(data["power"]))
                contract_line.name.replace("#coefficient#", str(data["coefficient"]))
                contract_line.name.replace(
                    "#power_acquired#", str(data["power_acquired"])
                )
                contract_line.name.replace(
                    "#days_invoiced#", str(data["days_invoiced"])
                )
                contract_line.name.replace("#total_amount#", str(data["total_amount"]))

    # TODO: DEPRECATED and not in use. Remove before merging branch
    def generate_contracts_button(self):
        """
        This method generates contracts based on supply point assignations.
        It first creates a product and a contract formula. It then
        aggregates supply point assignations by partner and owner
        to generate the contracts.
        In the other hand, if the process was successful, the state of self-consumption
        and the distribution_table changes to 'active'.

        Returns:
            bool: Always True, indicating successful execution.

        Raises:
            UserWarning: When no accounting journal is found.
            SomeException: When no distribution table in process of activation is found.
        """
        # Get distribution table
        distribution_id = (
            self.selfconsumption_id.distribution_table_ids.filtered_domain(
                [("state", "=", "process")]
            )
        )
        if not distribution_id:
            raise _("There is no distribution table in proces of activation.")

        # Create contracts
        for supply_point_assignation in distribution_id.supply_point_assignation_ids:
            # We write the date_start on the template, so it is not overwrite from the template
            self.selfconsumption_id.product_id.contract_template_id.write(
                {
                    "date_start": self.start_date,
                    "recurring_next_date": self.start_date,
                }
            )

            inscription_id = self.selfconsumption_id.inscription_ids.filtered_domain(
                [
                    (
                        "partner_id",
                        "=",
                        supply_point_assignation.supply_point_id.partner_id.id,
                    )
                ]
            )

            if not inscription_id.mandate_id:
                raise ValidationError(
                    _("Mandate not found for {partner}").format(
                        partner=supply_point_assignation.supply_point_id.partner_id.name
                    )
                )

            contract = self.env["contract.contract"].create(
                {
                    "name": _("Contract - %s - %s")
                    % (
                        self.selfconsumption_id.name,
                        supply_point_assignation.supply_point_id.partner_id.name,
                    ),
                    "partner_id": supply_point_assignation.supply_point_id.partner_id.id,
                    "supply_point_assignation_id": supply_point_assignation.id,
                    "company_id": self.env.company.id,
                    "contract_template_id": self.selfconsumption_id.product_id.contract_template_id.id,
                    "payment_mode_id": self.payment_mode.id,
                    "mandate_id": inscription_id.mandate_id.id,
                }
            )
            # We use the next method from the contract model to update the contract fields with contract template
            contract._onchange_contract_template_id()
            for contract_line_id in contract.contract_line_ids:
                data = {
                    "code": supply_point_assignation.supply_point_id.code,
                    "owner_id": supply_point_assignation.supply_point_id.owner_id.display_name,
                    "cau": self.selfconsumption_id.code,
                }
                # Each invoicing type has different data in the description column, so we need to check and modify
                if self.selfconsumption_id.invoicing_mode == "energy_delivered":
                    contract_line_id.name += """\nCAU: {cau}\n"""
                elif self.selfconsumption_id.invoicing_mode == "power_acquired":
                    contract_line_id.name += _(
                        """\nCAU: {cau}
                        Total installed nominal power (kW): {power}
                        Partition coefficient: {coefficient}
                        Daily nominal power acquired: {power} kWn * {coefficient} = {power_acquired} kWn/day
                        Days to be invoiced: {days_invoiced} days
                        Total amount invoiced:  {days_invoiced} days * {power_acquired} kWn/day = {total_amount}\n"""
                    )
                    data["power"] = self.selfconsumption_id.power
                    data["coefficient"] = supply_point_assignation.coefficient
                    (
                        first_date_invoiced,
                        last_date_invoiced,
                        recurring_next_date,
                    ) = contract_line_id._get_period_to_invoice(
                        contract_line_id.last_date_invoiced,
                        contract_line_id.recurring_next_date,
                    )
                    data["days_invoiced"] = (
                        (last_date_invoiced - first_date_invoiced).days + 1
                        if first_date_invoiced and last_date_invoiced
                        else 0
                    )
                    data["power_acquired"] = (
                        round(
                            self.selfconsumption_id.power
                            * supply_point_assignation.coefficient,
                            2,
                        )
                        if supply_point_assignation.coefficient
                        else 0.0
                    )
                    data["total_amount"] = round(
                        data["days_invoiced"] * data["power_acquired"], 2
                    )

                contract_line_id.write(
                    {"name": contract_line_id.name.format(**data), "main_line": True}
                )
        # Update selfconsumption and distribution_table state
        self.selfconsumption_id.write({"state": "active"})
        self.selfconsumption_id.distribution_table_state("process", "active")
        return True
