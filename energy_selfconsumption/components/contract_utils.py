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

    def _set_resting_metadata_in_contract(self, metadata_keys_arr):
        # Fields that should not be auto-updated for self-consumption contracts
        fields_to_remove = [
            "selfconsumption_id",  # Self-consumption project reference
            "supply_point_id",  # Supply point reference
        ]
        for field in fields_to_remove:
            if field in metadata_keys_arr:
                metadata_keys_arr.remove(field)
                logger.debug(f"Removed field '{field}' from contract update dictionary")
        super()._set_resting_metadata_in_contract(metadata_keys_arr)

    # TODO: Remove all this if we're not going to use it
    # # Utility methods for contract management
    # def get_selfconsumption_contract_fields(self):
    #     """
    #     Get list of fields specific to self-consumption contracts
    #     Returns:
    #         list: List of field names specific to self-consumption contracts
    #     """
    #     return [
    #         "selfconsumption_id",
    #         "supply_point_id",
    #         "distribution_table_id",
    #         "participation_quantity",
    #     ]
    # def validate_selfconsumption_contract_setup(self, contract):
    #     """
    #     Validate self-consumption contract setup
    #     Args:
    #         contract: Contract record to validate
    #     Returns:
    #         bool: True if contract setup is valid
    #     Raises:
    #         ValidationError: If contract setup is invalid
    #     """
    #     if not contract:
    #         return False
    #     # Check if contract has self-consumption project
    #     if hasattr(contract, "selfconsumption_id") and contract.selfconsumption_id:
    #         logger.info(
    #             f"Contract {contract.id} is linked to self-consumption project {contract.selfconsumption_id.id}"
    #         )
    #         return True
    #     return False
