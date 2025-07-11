from odoo import fields, models

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.energy_communities_service_invoicing.config import (
    CONTRACT_STATUS_IN_PROGRESS,
)


class EnergyProject(models.Model):
    """
    Energy Project Model Extension for Self-consumption

    This model extends the base energy project functionality to support
    self-consumption projects, including:
    - Self-consumption project relationships
    - Contract management and filtering
    - Member contract retrieval
    - Integration with energy communities
    """

    _inherit = "energy_project.project"

    # Self-consumption relationships
    selfconsumption_id = fields.One2many(
        "energy_selfconsumption.selfconsumption",
        "project_id",
        help="Self-consumption projects associated with this energy project",
    )
    contract_ids = fields.One2many(
        "contract.contract",
        "project_id",
        readonly=True,
        help="Contracts associated with this energy project",
    )

    # Business logic methods
    def get_member_contract(self, member: Partner):
        """
        Get active contract for a specific member

        Retrieves the contract for a given partner that is currently
        in progress status.

        Args:
            member (Partner): Partner record to find contract for

        Returns:
            contract.contract: Active contract record or empty recordset
        """
        self.ensure_one()

        if not member:
            return self.env["contract.contract"]

        # Filter contracts for the specific member with in-progress status
        member_contract = self.contract_ids.filtered(
            lambda contract: contract.partner_id == member
            and contract.status == CONTRACT_STATUS_IN_PROGRESS
        )

        return member_contract

    def get_selfconsumption_project(self):
        """
        Get the main self-consumption project for this energy project

        Returns:
            selfconsumption: Main self-consumption project or False
        """
        self.ensure_one()
        return self.selfconsumption_id[0] if self.selfconsumption_id else False

    def get_active_contracts(self):
        """
        Get all active contracts for this project

        Returns:
            recordset: Active contracts with in-progress status
        """
        self.ensure_one()
        return self.contract_ids.filtered(
            lambda contract: contract.status == CONTRACT_STATUS_IN_PROGRESS
        )

    def get_contracts_by_status(self, status):
        """
        Get contracts filtered by specific status

        Args:
            status (str): Contract status to filter by

        Returns:
            recordset: Contracts with the specified status
        """
        self.ensure_one()
        return self.contract_ids.filtered(lambda contract: contract.status == status)

    def get_member_count(self):
        """
        Get total number of unique members with contracts

        Returns:
            int: Number of unique partners with contracts
        """
        self.ensure_one()
        return len(self.contract_ids.mapped("partner_id"))

    def get_active_member_count(self):
        """
        Get number of members with active contracts

        Returns:
            int: Number of unique partners with active contracts
        """
        self.ensure_one()
        active_contracts = self.get_active_contracts()
        return len(active_contracts.mapped("partner_id"))

    def has_selfconsumption_project(self):
        """
        Check if this energy project has associated self-consumption projects

        Returns:
            bool: True if has self-consumption projects, False otherwise
        """
        self.ensure_one()
        return bool(self.selfconsumption_id)

    def get_project_summary(self):
        """
        Get summary information about the project

        Returns:
            dict: Summary with project statistics
        """
        self.ensure_one()
        selfconsumption = self.get_selfconsumption_project()

        return {
            "name": self.name,
            "has_selfconsumption": self.has_selfconsumption_project(),
            "selfconsumption_state": selfconsumption.state if selfconsumption else None,
            "total_contracts": len(self.contract_ids),
            "active_contracts": len(self.get_active_contracts()),
            "total_members": self.get_member_count(),
            "active_members": self.get_active_member_count(),
        }
