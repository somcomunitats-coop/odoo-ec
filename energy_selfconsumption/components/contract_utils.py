# Copyright 2024 Coopdevs Treball SCCL & Som Energia SCCL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component

logger = logging.getLogger(__name__)


class ContractUtils(Component):
    """
    Contract Utilities Component

    This component extends the base contract utilities to provide
    specialized functionality for energy self-consumption projects.

    Features:
    - Contract setup customization for self-consumption projects
    - Supply point integration with contract management
    - Specialized field handling for energy community contracts
    - Integration with energy communities framework
    """

    _inherit = "contract.utils"

    def _setup_contract_get_update_dict_initial(self):
        """
        Get initial contract update dictionary with self-consumption customizations

        This method extends the base contract setup to handle specific fields
        related to self-consumption projects and supply points that should not
        be automatically updated during contract setup.

        Returns:
            dict: Contract update dictionary with self-consumption fields excluded
        """
        try:
            # Get base contract update dictionary
            contract_update_dict = super()._setup_contract_get_update_dict_initial()

            # Remove self-consumption specific fields that should not be auto-updated
            self._remove_selfconsumption_fields(contract_update_dict)

            return contract_update_dict

        except Exception as e:
            logger.error(f"Error setting up contract update dictionary: {e}")
            # Return base dictionary as fallback
            return super()._setup_contract_get_update_dict_initial()

    def _remove_selfconsumption_fields(self, contract_update_dict):
        """
        Remove self-consumption specific fields from contract update dictionary

        These fields are managed separately and should not be automatically
        updated during standard contract setup operations.

        Args:
            contract_update_dict (dict): Contract update dictionary to modify
        """
        # Fields that should not be auto-updated for self-consumption contracts
        fields_to_remove = [
            "selfconsumption_id",  # Self-consumption project reference
            "supply_point_id",  # Supply point reference
        ]

        for field in fields_to_remove:
            if field in contract_update_dict:
                del contract_update_dict[field]
                logger.debug(f"Removed field '{field}' from contract update dictionary")

    # Utility methods for contract management
    def get_selfconsumption_contract_fields(self):
        """
        Get list of fields specific to self-consumption contracts

        Returns:
            list: List of field names specific to self-consumption contracts
        """
        return [
            "selfconsumption_id",
            "supply_point_id",
            "distribution_table_id",
            "participation_quantity",
        ]

    def validate_selfconsumption_contract_setup(self, contract):
        """
        Validate self-consumption contract setup

        Args:
            contract: Contract record to validate

        Returns:
            bool: True if contract setup is valid

        Raises:
            ValidationError: If contract setup is invalid
        """
        if not contract:
            return False

        # Check if contract has self-consumption project
        if hasattr(contract, "selfconsumption_id") and contract.selfconsumption_id:
            logger.info(
                f"Contract {contract.id} is linked to self-consumption project {contract.selfconsumption_id.id}"
            )
            return True

        return False
