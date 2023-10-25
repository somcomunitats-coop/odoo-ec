from odoo import _, fields, models


class ContractGenerationWizard(models.TransientModel):
    _name = "energy_selfconsumption.contract_generation.wizard"

    selfconsumption_id = fields.Many2one(
        "energy_selfconsumption.selfconsumption", readonly=True
    )

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

        product_id = self.selfconsumption_id.product_id
        formula_contract_id = (
            self.selfconsumption_id.product_id.contract_template_id.contract_line_ids.qty_formula_id
        )

        # Search accounting journal
        journal_id = self.env["account.journal"].search(
            [("company_id", "=", self.env.company.id), ("type", "=", "sale")], limit=1
        )
        if not journal_id:
            raise UserWarning(_("Accounting Journal not found."))

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
            contract = self.env["contract.contract"].create(
                {
                    "name": _("Contract - %s - %s")
                    % (
                        self.selfconsumption_id.name,
                        supply_point_assignation.supply_point_id.partner_id.name,
                    ),
                    "partner_id": supply_point_assignation.supply_point_id.partner_id.id,
                    "journal_id": journal_id.id,
                    "recurring_interval": self.selfconsumption_id.product_id.contract_template_id.recurring_interval,
                    "recurring_rule_type": self.selfconsumption_id.product_id.contract_template_id.recurring_rule_type,
                    "recurring_invoicing_type": "post-paid",
                    "date_start": fields.date.today(),
                    "contract_template_id": self.selfconsumption_id.product_id.contract_template_id.id,
                }
            )
            contract._onchange_contract_template_id()
        # Update selfconsumption and distribution_table state
        self.selfconsumption_id.write({"state": "active"})
        self.selfconsumption_id.distribution_table_state("process", "active")
        return True
