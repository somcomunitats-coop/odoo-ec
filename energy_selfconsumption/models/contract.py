from collections import namedtuple

from odoo import fields, models

from ..config import SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED

# Constants for contract management
ARKENOVA_PROVIDER_PATTERN = "%Arkenova%"
DISTRIBUTION_TABLE_STATE_ACTIVE = "active"


class Contract(models.Model):
    """
    Contract Model Extension for Self-consumption

    This model extends the base contract functionality to support
    self-consumption energy projects, including:
    - Supply point assignation relationships
    - Energy project integration
    - Invoicing wizard integration
    - Period tracking for recurring invoices
    - Monitoring member counting
    - Custom invoicing domain filtering
    """

    _inherit = "contract.contract"

    # Self-consumption specific fields
    supply_point_assignation_id = fields.Many2one(
        "energy_selfconsumption.supply_point_assignation",
        string="Supply point assignation",
        help="Supply point assignation this contract is based on",
    )

    # TODO: Move this field into energy_project module
    project_id = fields.Many2one(
        "energy_project.project",
        ondelete="restrict",
        string="Energy Project",
        related="supply_point_assignation_id.distribution_table_id.selfconsumption_project_id.project_id",
        store=True,
        auto_join=True,
        help="Energy project associated with this contract",
    )

    # Related supply point information
    code = fields.Char(
        related="supply_point_assignation_id.supply_point_id.code",
        help="CUPS code of the associated supply point",
    )
    supply_point_name = fields.Char(
        related="supply_point_assignation_id.supply_point_id.name",
        help="Name of the associated supply point",
    )

    # Business logic methods
    def get_main_line(self):
        """
        Get the main contract line for this contract

        Returns:
            contract.line: Main contract line record
        """
        self.ensure_one()
        main_line_record = self.contract_line_ids.filtered(lambda line: line.main_line)
        return main_line_record

    def invoicing_wizard_action(self):
        """
        Open invoicing wizard for this contract

        Creates the wizard first to trigger contract validation constraints,
        then returns the window action with the wizard already created.

        Returns:
            dict: Window action dictionary for the invoicing wizard
        """
        # Get invoicing mode from first contract
        invoicing_mode = False
        contracts = self.env["contract.contract"].search([("id", "in", self.ids)])
        if contracts:
            invoicing_mode = (
                contracts[0].project_id.selfconsumption_id.invoicing_mode or False
            )

        # Create wizard with current contract
        wizard_id = (
            self.env["energy_selfconsumption.invoicing.wizard"]
            .with_context(active_ids=self.ids)
            .create(
                {
                    "contract_ids": [(6, 0, self.ids)],
                    "invoicing_mode": invoicing_mode,
                }
            )
        )

        # Get action reference and update with wizard ID
        action = self.env.ref(
            "energy_selfconsumption.invoicing_wizard_act_window"
        ).read()[0]
        action["res_id"] = wizard_id.id

        return action

    def _get_contracts_to_invoice_domain(self, date_ref=None):
        """
        Override contract invoicing domain to exclude energy delivered mode

        Extends the base domain to exclude contracts from projects with
        'energy_delivered' invoicing mode, as these are handled separately.

        Args:
            date_ref: Reference date for filtering

        Returns:
            list: Domain filter for contracts to invoice
        """
        domain = super()._get_contracts_to_invoice_domain(date_ref)

        # Exclude contracts with energy_delivered invoicing mode
        domain.extend(
            [
                (
                    "project_id.selfconsumption_id.invoicing_mode",
                    "!=",
                    SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED,
                )
            ]
        )

        return domain

    def get_active_monitoring_members(self):
        """
        Get count of active monitoring members for Arkenova provider

        Executes a complex SQL query to count active supply points
        in self-consumption projects with Arkenova monitoring service.

        Returns:
            int: Number of active monitoring members
        """
        # Define named tuple for query result
        QueryResult = namedtuple("QueryResult", ["total"])

        # Build SQL query for active monitoring members
        query = """
            SELECT COUNT(energy_selfconsumption_supply_point.code)
            FROM energy_project_project
            INNER JOIN energy_selfconsumption_selfconsumption ON
                energy_selfconsumption_selfconsumption.project_id = energy_project_project.id
            INNER JOIN energy_selfconsumption_distribution_table ON
                energy_selfconsumption_distribution_table.selfconsumption_project_id = energy_selfconsumption_selfconsumption.id
            INNER JOIN energy_selfconsumption_supply_point_assignation ON
                energy_selfconsumption_supply_point_assignation.distribution_table_id = energy_selfconsumption_distribution_table.id
            INNER JOIN energy_selfconsumption_supply_point ON
                energy_selfconsumption_supply_point.id = energy_selfconsumption_supply_point_assignation.supply_point_id
            INNER JOIN energy_project_service_contract ON
                energy_project_service_contract.project_id = energy_project_project.id
            INNER JOIN energy_project_provider ON
                energy_project_service_contract.provider_id = energy_project_provider.id
            WHERE
                energy_project_project.company_id = %s AND
                energy_selfconsumption_distribution_table.state = %s AND
                energy_project_provider.name LIKE %s
        """

        # Execute query with parameters
        self.env.cr.execute(
            query,
            [
                int(self.community_company_id.id),
                DISTRIBUTION_TABLE_STATE_ACTIVE,
                ARKENOVA_PROVIDER_PATTERN,
            ],
        )

        # Return count result
        members = QueryResult._make(self.env.cr.fetchone())
        return members.total

    # Utility methods
    def is_selfconsumption_contract(self):
        """
        Check if this is a self-consumption contract

        Returns:
            bool: True if contract has supply point assignation, False otherwise
        """
        self.ensure_one()
        return bool(self.supply_point_assignation_id)

    def get_distribution_table(self):
        """
        Get the distribution table associated with this contract

        Returns:
            distribution_table: Distribution table record or False
        """
        self.ensure_one()
        if self.supply_point_assignation_id:
            return self.supply_point_assignation_id.distribution_table_id
        return False

    def get_selfconsumption_project(self):
        """
        Get the self-consumption project for this contract

        Returns:
            selfconsumption: Self-consumption project record or False
        """
        self.ensure_one()
        distribution_table = self.get_distribution_table()
        if distribution_table:
            return distribution_table.selfconsumption_project_id
        return False

    def get_supply_point(self):
        """
        Get the supply point associated with this contract

        Returns:
            supply_point: Supply point record or False
        """
        self.ensure_one()
        if self.supply_point_assignation_id:
            return self.supply_point_assignation_id.supply_point_id
        return False

    def get_partner_display_info(self):
        """
        Get formatted partner information for display

        Returns:
            dict: Partner information dictionary
        """
        self.ensure_one()
        supply_point = self.get_supply_point()

        if supply_point:
            return {
                "cooperator": supply_point.partner_id.name
                if supply_point.partner_id
                else "",
                "owner": supply_point.owner_id.name if supply_point.owner_id else "",
                "cups": supply_point.code or "",
                "address": supply_point.get_display_address(),
            }

        return {
            "cooperator": "",
            "owner": "",
            "cups": "",
            "address": "",
        }


class ContractRecurrencyMixin(models.AbstractModel):
    """
    Contract Recurrency Mixin Extension

    Extends the base contract recurrency mixin to add stored
    next period date fields for better performance and tracking.
    """

    _inherit = "contract.recurrency.mixin"

    # Stored period date fields for performance
    next_period_date_start = fields.Date(
        store=True, help="Start date of the next period to be invoiced"
    )
    next_period_date_end = fields.Date(
        store=True, help="End date of the next period to be invoiced"
    )
