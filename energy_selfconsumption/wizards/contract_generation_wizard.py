from odoo import _, fields, models


class ContractGenerationWizard(models.TransientModel):
    _name = "energy_selfconsumption.contract_generation.wizard"

    price_energy = fields.Float(string="Price (€/kWn/day)")

    recurring_interval = fields.Integer(
        default=1,
        string="Invoice Every",
        help="Invoice every (Days/Week/Month/Year)",
    )
    recurring_rule_type = fields.Selection(
        [
            ("daily", "Day(s)"),
            ("weekly", "Week(s)"),
            ("monthly", "Month(s)"),
            ("monthlylastday", "Month(s) last day"),
            ("quarterly", "Quarter(s)"),
            ("semesterly", "Semester(s)"),
            ("yearly", "Year(s)"),
        ],
        default="monthly",
        string="Recurrence",
        help="Specify Interval for automatic invoice generation.",
    )
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

        # Create product
        product_id = self.env["product.product"].create(
            {
                "name": _("Energy Acquired - %s") % (self.selfconsumption_id.name),
                "lst_price": self.price_energy,
                "company_id": self.env.company.id,
            }
        )

        # Create contract formula
        formula_contract_id = self.env["contract.line.qty.formula"].create(
            {
                "name": _("Formula - %s") % (self.selfconsumption_id.name),
                "code": """
days_timedelta = line.next_period_date_end - line.next_period_date_start
if days_timedelta:
  # Add one so it counts the same day too (month = 29 + 1)
  days_between = days_timedelta.days + 1
else:
  days_between = 0
result = line.supply_point_assignation_id.distribution_table_id.selfconsumption_project_id.power * line.supply_point_assignation_id.coefficient * days_between
                """,
            }
        product_id = self.selfconsumption_id.product_id
        formula_contract_id = (
            self.selfconsumption_id.contract_template_id.contract_line_ids.qty_formula_id
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
            contract_lines = [
                (
                    0,
                    0,
                    {
                        "product_id": product_id.id,
                        "automatic_price": True,
                        "company_id": self.env.company.id,
                        "qty_type": "variable",
                        "qty_formula_id": formula_contract_id.id,
                        "name": _(
                            """CUPS: %s
                        Owner: %s
                        Invoicing period: #START# - #END#"""
                        )
                        % (
                            supply_point_assignation.supply_point_id.code,
                            supply_point_assignation.supply_point_id.owner_id.display_name,
                        ),
                        "supply_point_assignation_id": supply_point_assignation.id,
                    },
                )
            ]

            self.env["contract.contract"].create(
                {
                    "name": _("Contract - %s - %s")
                    % (
                        self.selfconsumption_id.name,
                        supply_point_assignation.supply_point_id.partner_id.name,
                    ),
                    "partner_id": supply_point_assignation.supply_point_id.partner_id.id,
                    "invoice_partner_id": supply_point_assignation.supply_point_id.partner_id.id,
                    "journal_id": journal_id.id,
                    "recurring_interval": self.recurring_interval,
                    "recurring_rule_type": self.recurring_rule_type,
                    "recurring_invoicing_type": "post-paid",
                    "date_start": fields.date.today(),
                    "company_id": self.env.company.id,
                    "contract_line_ids": contract_lines,
                    "project_id": self.selfconsumption_id.project_id.id,
                }
            )

        # Update selfconsumption and distribution_table state
        self.selfconsumption_id.write({"state": "active"})
        self.selfconsumption_id.distribution_table_state("process", "active")
        return True
