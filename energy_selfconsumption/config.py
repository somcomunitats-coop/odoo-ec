"""
Configuration constants for energy self-consumption module

This module centralizes all configuration constants used throughout
the energy self-consumption module to improve maintainability and
reduce magic numbers/strings.
"""

from odoo import _

# Configuration state constants
from odoo.addons.energy_communities.config import (
    STATE_ACTIVE,
    STATE_CANCELLED,
    STATE_CHANGE,
    STATE_DRAFT,
    STATE_INACTIVE,
    STATE_LABELS,
    STATE_NONE,
    STATE_PROCESS,
    STATE_VALIDATED,
)

# Invoicing mode constants
SELFCONSUMPTION_INVOICING_MODE_NONE = STATE_NONE
SELFCONSUMPTION_INVOICING_MODE_POWER_ACQUIRED = "power_acquired"
SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED = "energy_delivered"
SELFCONSUMPTION_INVOICING_MODE_ENERGY_CUSTOM = "energy_custom"

SELFCONSUMPTION_INVOICING_MODE_LABELS = {
    SELFCONSUMPTION_INVOICING_MODE_NONE: STATE_LABELS[
        SELFCONSUMPTION_INVOICING_MODE_NONE
    ],
    SELFCONSUMPTION_INVOICING_MODE_POWER_ACQUIRED: _("Power Acquired"),
    SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED: _("Energy Delivered"),
    SELFCONSUMPTION_INVOICING_MODE_ENERGY_CUSTOM: _("Energy Delivered Custom"),
}

SELFCONSUMPTION_INVOICING_MODE_VALUES = [
    (
        SELFCONSUMPTION_INVOICING_MODE_POWER_ACQUIRED,
        SELFCONSUMPTION_INVOICING_MODE_LABELS[
            SELFCONSUMPTION_INVOICING_MODE_POWER_ACQUIRED
        ],
    ),
    (
        SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED,
        SELFCONSUMPTION_INVOICING_MODE_LABELS[
            SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED
        ],
    ),
    (
        SELFCONSUMPTION_INVOICING_MODE_ENERGY_CUSTOM,
        SELFCONSUMPTION_INVOICING_MODE_LABELS[
            SELFCONSUMPTION_INVOICING_MODE_ENERGY_CUSTOM
        ],
    ),
]

SELFCONSUMPTION_DEFAULT_INVOICING_MODE = SELFCONSUMPTION_INVOICING_MODE_POWER_ACQUIRED

# Contract recurrency invoicing types (contract module values)
RECURRING_INVOICING_TYPE_PREPAID = "pre-paid"
RECURRING_INVOICING_TYPE_POSTPAID = "post-paid"

# Product template references
SELFCONSUMPTION_PRODUCT_REFS = {
    SELFCONSUMPTION_INVOICING_MODE_POWER_ACQUIRED: {
        "template": "energy_selfconsumption.product_product_power_acquired_product_template",
        "pack": "energy_selfconsumption.product_product_power_acquired_product_pack_template",
    },
    SELFCONSUMPTION_INVOICING_MODE_ENERGY_DELIVERED: {
        "template": "energy_selfconsumption.product_product_energy_delivered_product_template",
        "pack": "energy_selfconsumption.product_product_energy_delivered_product_pack_template",
    },
    SELFCONSUMPTION_INVOICING_MODE_ENERGY_CUSTOM: {
        "template": "energy_selfconsumption.product_product_energy_custom_product_template",
        "pack": "energy_selfconsumption.product_product_energy_custom_product_pack_template",
    },
}

# STATES
SELFCONSUMPTION_CONF_STATE_ACTIVE = STATE_ACTIVE
SELFCONSUMPTION_CONF_STATE_INACTIVE = STATE_INACTIVE

SELFCONSUMPTION_CONF_STATE_VALUES = [
    (
        SELFCONSUMPTION_CONF_STATE_ACTIVE,
        STATE_LABELS[SELFCONSUMPTION_CONF_STATE_ACTIVE],
    ),
    (
        SELFCONSUMPTION_CONF_STATE_INACTIVE,
        STATE_LABELS[SELFCONSUMPTION_CONF_STATE_INACTIVE],
    ),
]
SELFCONSUMPTION_CONF_STATE_DEFAULT_VALUE = SELFCONSUMPTION_CONF_STATE_INACTIVE

# Inscription state constants
INSCRIPTION_STATE_ACTIVE = STATE_ACTIVE
INSCRIPTION_STATE_INACTIVE = STATE_INACTIVE
INSCRIPTION_STATE_CHANGE = STATE_CHANGE
INSCRIPTION_STATE_CANCELLED = STATE_CANCELLED

INSCRIPTION_STATE_VALUES = [
    (INSCRIPTION_STATE_ACTIVE, STATE_LABELS[INSCRIPTION_STATE_ACTIVE]),
    (INSCRIPTION_STATE_INACTIVE, STATE_LABELS[INSCRIPTION_STATE_INACTIVE]),
    (INSCRIPTION_STATE_CHANGE, STATE_LABELS[INSCRIPTION_STATE_CHANGE]),
    (INSCRIPTION_STATE_CANCELLED, STATE_LABELS[INSCRIPTION_STATE_CANCELLED]),
]
INSCRIPTION_STATE_DEFAULT_VALUE = INSCRIPTION_STATE_INACTIVE

# Distribution table state constants
DISTRIBUTION_STATE_DRAFT = STATE_DRAFT
DISTRIBUTION_STATE_PROCESS = STATE_PROCESS
DISTRIBUTION_STATE_VALIDATED = STATE_VALIDATED
DISTRIBUTION_STATE_ACTIVE = STATE_ACTIVE
DISTRIBUTION_STATE_CANCELLED = STATE_CANCELLED

DISTRIBUTION_STATE_VALUES = [
    (DISTRIBUTION_STATE_DRAFT, STATE_LABELS[DISTRIBUTION_STATE_DRAFT]),
    (DISTRIBUTION_STATE_VALIDATED, STATE_LABELS[DISTRIBUTION_STATE_VALIDATED]),
    (DISTRIBUTION_STATE_PROCESS, STATE_LABELS[DISTRIBUTION_STATE_PROCESS]),
    (DISTRIBUTION_STATE_ACTIVE, STATE_LABELS[DISTRIBUTION_STATE_ACTIVE]),
    (DISTRIBUTION_STATE_CANCELLED, STATE_LABELS[DISTRIBUTION_STATE_CANCELLED]),
]
DISTRIBUTION_STATE_DEFAULT_VALUE = DISTRIBUTION_STATE_DRAFT

# Distribution table type constants
DISTRIBUTION_TYPE_FIXED = "fixed"
DISTRIBUTION_TYPE_HOURLY = "hourly"

DISTRIBUTION_TYPE_VALUES = [
    (DISTRIBUTION_TYPE_FIXED, _("Fixed")),
    (DISTRIBUTION_TYPE_HOURLY, _("Variable hourly")),
]

DISTRIBUTION_TYPE_DEFAULT_VALUE = DISTRIBUTION_TYPE_FIXED

# CAU and CIL validation constants
CAU_LENGTH_24 = 24
CAU_LENGTH_26 = 26
CIL_LENGTH_23 = 23
CIL_LENGTH_25 = 25
CUPS_LENGTH_20 = 20
CUPS_LENGTH_22 = 22
CAU_SEPARATOR = "A"
LAST_DIGITS_COUNT = 3

# Tariff constants. Codes have no space between the number and the letters.
TARIFF_2_0TD = "2.0TD"
TARIFF_3_0TD = "3.0TD"
TARIFF_3_0TDVE = "3.0TDVE"
TARIFF_6_1TD = "6.1TD"
TARIFF_6_1TDVE = "6.1TDVE"
TARIFF_6_2TD = "6.2TD"
TARIFF_6_2TDVE = "6.2TDVE"
TARIFF_6_3TD = "6.3TD"
TARIFF_6_4TD = "6.4TD"

# Alphabetical order used by the supply point and the public form.
ACCESS_TARIFF_VALUES = [
    (TARIFF_2_0TD, TARIFF_2_0TD),
    (TARIFF_3_0TD, TARIFF_3_0TD),
    (TARIFF_3_0TDVE, TARIFF_3_0TDVE),
    (TARIFF_6_1TD, TARIFF_6_1TD),
    (TARIFF_6_1TDVE, TARIFF_6_1TDVE),
    (TARIFF_6_2TD, TARIFF_6_2TD),
    (TARIFF_6_2TDVE, TARIFF_6_2TDVE),
    (TARIFF_6_3TD, TARIFF_6_3TD),
    (TARIFF_6_4TD, TARIFF_6_4TD),
]

# Electric-vehicle tariffs are never inferred from contracted power.
VEHICLE_ACCESS_TARIFFS = {
    TARIFF_3_0TDVE,
    TARIFF_6_1TDVE,
    TARIFF_6_2TDVE,
}

TARIFF_POWER_LIMITS = {
    TARIFF_2_0TD: 15,  # kW
    TARIFF_3_0TD: 300,  # kW
}

PARTICIPATION_HELP_HTML_BY_LANG = {
    "en_US": (
        "<p>The usual recommendation for an annual electrical use of is 0.5kW "
        "of PV power per 1500 kWh of electrical consumption.</p>"
        "<p>1000 - 1500 kWh a maximum of 0.5 kW of participation is recommended</p>"
        "<p>1500 - 3000 kWh between 0.5 and 1 kW</p>"
        "<p>3000 - 5000 kWh between 1.5 - 2 kW</p>"
    ),
    "es_ES": (
        "<p>La recomendación habitual para un uso eléctrico anual es de 0,5 kW "
        "de energía fotovoltaica de potencia por 1500 kWh de consumo eléctrico.</p>"
        "<p>1000 - 1500 kWh se recomienda un máximo de 0,5 kW de participación</p>"
        "<p>1500 - 3000 kWh entre 0,5 y 1 kW</p>"
        "<p>3000 - 5000 kWh entre 1,5 - 2 kW</p>"
    ),
    "ca_ES": (
        "<p>La recomanació habitual per a un ús elèctric anual de 0,5 kW de FV "
        "potència per 1500 kWh de consum elèctric.</p>"
        "<p>1000 - 1500 kWh es recomana un màxim de 0,5 kW de participació</p>"
        "<p>1500 - 3000 kWh entre 0,5 i 1 kW</p>"
        "<p>3000 - 5000 kWh entre 1,5 - 2 kW</p>"
    ),
    "eu_ES": (
        "<p>Urteko erabilera elektrikorako ohiko gomendioa PV 0,5 kW da "
        "potentzia kontsumo elektrikoko 1500 kWh bakoitzeko.</p>"
        "<p>1000 - 1500 kWh gehienez 0,5 kW parte hartzea gomendatzen da</p>"
        "<p>1500 - 3000 kWh 0,5 eta 1 kW artean</p>"
        "<p>3000 - 5000 kWh 1,5 - 2 kW artean</p>"
    ),
}

# Power validation constants
MIN_POWER_VALUE = 0.0
MAX_POWER_VALUE = 10000.0  # 10 MW

# CSV processing constants
CSV_DELIMITER = ","
CSV_QUOTE_CHAR = '"'
CSV_FILE_EXTENSION = "csv"
DEFAULT_ENCODING = "utf-8"

# Default participation options for new projects
DEFAULT_PARTICIPATIONS = [
    {"name": "1.0 kW", "quantity": 1.0},
    {"name": "2.0 kW", "quantity": 2.0},
    {"name": "3.0 kW", "quantity": 3.0},
    {"name": "5.0 kW", "quantity": 5.0},
]
SELFCONSUMPTION_DEFAULT_PARTICIPATIONS = [
    {"name": "0,5 kW", "quantity": 0.5},
    {"name": "1,0 kW", "quantity": 1.0},
    {"name": "1,5 kW", "quantity": 1.5},
    {"name": "2,0 kW", "quantity": 2.0},
]
