"""
Configuration constants for energy self-consumption module

This module centralizes all configuration constants used throughout
the energy self-consumption module to improve maintainability and
reduce magic numbers/strings.
"""

from odoo import _

# Invoicing mode constants
INVOICING_MODE_NONE = "none"
INVOICING_MODE_POWER_ACQUIRED = "power_acquired"
INVOICING_MODE_ENERGY_DELIVERED = "energy_delivered"
INVOICING_MODE_ENERGY_CUSTOM = "energy_custom"

INVOICING_VALUES = [
    (INVOICING_MODE_POWER_ACQUIRED, _("Power Acquired")),
    (INVOICING_MODE_ENERGY_DELIVERED, _("Energy Delivered")),
    (INVOICING_MODE_ENERGY_CUSTOM, _("Energy Delivered Custom")),
]

# Configuration state constants
STATE_ACTIVE = "active"
STATE_INACTIVE = "inactive"

CONF_STATE_VALUES = [
    (STATE_ACTIVE, _("Active")),
    (STATE_INACTIVE, _("Inactive")),
]

# Project state constants
PROJECT_STATE_DRAFT = "draft"
PROJECT_STATE_INSCRIPTION = "inscription"
PROJECT_STATE_ACTIVATION = "activation"
PROJECT_STATE_ACTIVE = "active"

# Inscription state constants
INSCRIPTION_STATE_ACTIVE = "active"
INSCRIPTION_STATE_INACTIVE = "inactive"
INSCRIPTION_STATE_CHANGE = "change"
INSCRIPTION_STATE_CANCELLED = "cancelled"

# Distribution table state constants
DISTRIBUTION_STATE_DRAFT = "draft"
DISTRIBUTION_STATE_PROCESS = "process"
DISTRIBUTION_STATE_VALIDATED = "validated"
DISTRIBUTION_STATE_ACTIVE = "active"
DISTRIBUTION_STATE_INACTIVE = "inactive"

# Distribution table type constants
DISTRIBUTION_TYPE_FIXED = "fixed"
DISTRIBUTION_TYPE_HOURLY = "hourly"

# CAU and CIL validation constants
CAU_LENGTH_24 = 24
CAU_LENGTH_26 = 26
CIL_LENGTH_23 = 23
CIL_LENGTH_25 = 25
CUPS_LENGTH_20 = 20
CUPS_LENGTH_22 = 22
CAU_SEPARATOR = "A"
LAST_DIGITS_COUNT = 3

# Tariff constants
TARIFF_2_0TD = "2.0TD"
TARIFF_3_0TD = "3.0TD"
TARIFF_6_1TD = "6.1TD"
TARIFF_6_2TD = "6.2TD"
TARIFF_6_3TD = "6.3TD"
TARIFF_6_4TD = "6.4TD"

TARIFF_POWER_LIMITS = {
    TARIFF_2_0TD: 15,  # kW
    TARIFF_3_0TD: 300,  # kW
}

# Pack type constants
PACK_TYPE_NONE = "none"
PACK_TYPE_SELFCONSUMPTION = "selfconsumption_pack"

# Contract status constants
CONTRACT_STATUS_DRAFT = "draft"
CONTRACT_STATUS_IN_PROGRESS = "in_progress"
CONTRACT_STATUS_TERMINATED = "terminated"

# Supply point constants
SUPPLY_POINT_ACTIVE = True
SUPPLY_POINT_INACTIVE = False

# Date format constants
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DISPLAY_DATE_FORMAT = "%d/%m/%Y"

# Power validation constants
MIN_POWER_VALUE = 0.0
MAX_POWER_VALUE = 10000.0  # 10 MW

# File processing constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_FILE_EXTENSIONS = [".csv", ".xlsx", ".xls"]

# CSV processing constants
CSV_DELIMITER = ","
CSV_QUOTE_CHAR = '"'
CSV_FILE_EXTENSION = "csv"
DEFAULT_ENCODING = "utf-8"

# Email template constants
TEMPLATE_ENERGY_DELIVERY_REMINDER = "energy_delivery_invoicing_reminder"
TEMPLATE_ENERGY_CUSTOM_REMINDER = "energy_delivery_custom_invoicing_reminder"
TEMPLATE_POWER_ACQUIRED_REMINDER = "power_acquired_invoicing_reminder"

# Report constants
REPORT_MANAGER_AUTHORIZATION = "manager_authorization_report"
REPORT_POWER_SHARING_AGREEMENT = "power_sharing_agreement_report"
REPORT_PARTITION_COEFFICIENT = "manager_partition_coefficient_report"

# Wizard constants
WIZARD_DEFINE_INVOICING_MODE = "energy_selfconsumption.define_invoicing_mode.wizard"
WIZARD_EXPORT_CSV_INSCRIPTIONS = "energy_selfconsumption.export_csv_inscriptions.wizard"
WIZARD_SET_IBAN_INSCRIPTIONS = "energy_selfconsumption.set_iban_inscriptions.wizard"
WIZARD_SELFCONSUMPTION_IMPORT = "energy_selfconsumption.selfconsumption_import.wizard"

# Model names constants
MODEL_SELFCONSUMPTION = "energy_selfconsumption.selfconsumption"
MODEL_DISTRIBUTION_TABLE = "energy_selfconsumption.distribution_table"
MODEL_INSCRIPTION = "energy_selfconsumption.inscription_selfconsumption"
MODEL_SUPPLY_POINT = "energy_selfconsumption.supply_point"
MODEL_PARTICIPATION = "energy_selfconsumptions.participation"
MODEL_CONTRACT = "contract.contract"
MODEL_PARTNER = "res.partner"
MODEL_COOPERATIVE_MEMBERSHIP = "cooperative.membership"

# Field validation constants
REQUIRED_INSCRIPTION_FIELDS = [
    "inscription_partner_id_vat",
    "supplypoint_cups",
    "supplypoint_contracted_power",
    "supplypoint_street",
    "supplypoint_city",
    "supplypoint_zip",
]

# Error message constants
ERROR_PARTNER_NOT_FOUND = "Partner with VAT:<b>{vat}</b> was not found."
ERROR_NOT_COOPERATOR = "Partner with VAT:<b>{vat}</b> is not a cooperator."
ERROR_ALREADY_REGISTERED = (
    "Partner with VAT {vat} is already registered in project {code}"
)
ERROR_OWNER_NOT_FOUND = "Owner could not be created or found."
ERROR_NO_PARTICIPATION = "No participation found for this project."

# Success message constants
SUCCESS_REGISTRATION = "You have successfully registered."

# View constants
VIEW_MODE_FORM = "form"
VIEW_MODE_TREE = "tree"
VIEW_MODE_KANBAN = "kanban"

# Action type constants
ACTION_TYPE_WINDOW = "ir.actions.act_window"
ACTION_TYPE_REPORT = "ir.actions.report"

# Default participation options for new projects
DEFAULT_PARTICIPATIONS = [
    {"name": "1.0 kW", "quantity": 1.0},
    {"name": "2.0 kW", "quantity": 2.0},
    {"name": "3.0 kW", "quantity": 3.0},
    {"name": "5.0 kW", "quantity": 5.0},
]
