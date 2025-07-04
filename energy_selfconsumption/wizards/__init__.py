"""
Energy Self-consumption Wizards

This package contains all wizard classes for the energy self-consumption module:
- Invoice generation and processing wizards
- Data import and export wizards
- Distribution table management wizards
- Contract generation and configuration wizards
- State management and cleaning wizards

All wizards follow best practices with comprehensive validation,
error handling, and English documentation.
"""

# Import all wizard modules
from . import contract_generation_wizard
from . import create_distribution_table_wizard
from . import define_invoicing_mode_wizard
from . import distribution_table_import_wizard
from . import invoicing_wizard
from . import selfconsumption_import_wizard
from . import change_state_inscription_wizard
from . import change_distribution_table_import_wizard
from . import set_iban_inscriptions_wizard
from . import export_csv_inscriptions_wizard
