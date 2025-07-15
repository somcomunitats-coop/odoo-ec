from odoo import _

# General
DISPLAY_DATE_FORMAT = "%d/%m/%Y"

# States
STATE_NONE = "none"
STATE_DRAFT = "draft"
STATE_ACTIVE = "active"
STATE_INACTIVE = "inactive"
STATE_PROCESS = "process"
STATE_VALIDATED = "validated"
STATE_CHANGE = "change"
STATE_CANCELLED = "cancelled"
STATE_INSCRIPTION = "inscription"
STATE_ACTIVATION = "activation"
STATE_PAUSED = "paused"
STATE_IN_PROGRESS = "in_progress"
STATE_CLOSED_PLANNED = "closed_planned"
STATE_CLOSED = "closed"

STATE_LABELS = {
    STATE_NONE: _("None"),
    STATE_DRAFT: _("Draft"),
    STATE_ACTIVE: _("Active"),
    STATE_INACTIVE: _("Inactive"),
    STATE_PROCESS: _("Process"),
    STATE_VALIDATED: _("Validated"),
    STATE_CHANGE: _("Change"),
    STATE_CANCELLED: _("Cancelled"),
    STATE_INSCRIPTION: _("Inscription"),
    STATE_ACTIVATION: _("In Activation"),
    STATE_PAUSED: _("Paused"),
    STATE_IN_PROGRESS: _("In progress"),
    STATE_CLOSED_PLANNED: _("Planned closure"),
    STATE_CLOSED: _("Closed"),
}

# Packs
PACK_TYPE_PLATFORM_PROD_CATEG_XMLID = (
    "energy_communities_service_invoicing.product_category_platform_pack"
)
PACK_TYPE_RECURRING_FEE_PROD_CATEG_XMLID = (
    "energy_communities.product_category_recurring_fee_pack"
)
PACK_TYPE_SHARE_RECURRING_FEE_PROD_CATEG_XMLID = (
    "energy_communities.product_category_share_recurring_fee_pack"
)
PACK_TYPE_SELFCONSUMPTION_PROD_CATEG_XMLID = (
    "energy_selfconsumption.product_category_selfconsumption_pack"
)

PACK_TYPE_NONE = STATE_NONE
PACK_TYPE_PLATFORM = "platform_pack"
PACK_TYPE_RECURRING_FEE = "recurring_fee_pack"
PACK_TYPE_SHARE_RECURRING_FEE = "share_recurring_fee_pack"
PACK_TYPE_SELFCONSUMPTION = "selfconsumption_pack"

PACK_TYPE_LABELS = {
    PACK_TYPE_NONE: STATE_LABELS[PACK_TYPE_NONE],
    PACK_TYPE_PLATFORM: _("Platform Pack"),
    PACK_TYPE_RECURRING_FEE: _("Recurring fee Pack"),
    PACK_TYPE_SHARE_RECURRING_FEE: _("Share with recurring fee pack"),
    PACK_TYPE_SELFCONSUMPTION: _("Selfconsumption Pack"),
}

PACK_TYPE_VALUES = [
    (PACK_TYPE_NONE, PACK_TYPE_LABELS[PACK_TYPE_NONE]),
    (PACK_TYPE_PLATFORM, PACK_TYPE_LABELS[PACK_TYPE_PLATFORM]),
    (PACK_TYPE_RECURRING_FEE, PACK_TYPE_LABELS[PACK_TYPE_RECURRING_FEE]),
    (PACK_TYPE_SHARE_RECURRING_FEE, PACK_TYPE_LABELS[PACK_TYPE_SHARE_RECURRING_FEE]),
    (PACK_TYPE_SELFCONSUMPTION, PACK_TYPE_LABELS[PACK_TYPE_SELFCONSUMPTION]),
]

PACK_TYPE_DEFAULT_VALUE = PACK_TYPE_NONE

PACK_PROD_CATEG_XMLID_REL_TO_SERVICE_PROD_CATEG_XMLID = {
    PACK_TYPE_RECURRING_FEE_PROD_CATEG_XMLID: "energy_communities.product_category_recurring_fee_service",
    PACK_TYPE_SHARE_RECURRING_FEE_PROD_CATEG_XMLID: "energy_communities.product_category_recurring_fee_service",
    PACK_TYPE_PLATFORM_PROD_CATEG_XMLID: "energy_communities_service_invoicing.product_category_platform_service",
    PACK_TYPE_SELFCONSUMPTION_PROD_CATEG_XMLID: "energy_selfconsumption.product_category_selfconsumption_service",
}

PACK_PROD_CATEG_XMLID_REL_TO_PACK_TYPES = {
    PACK_TYPE_RECURRING_FEE_PROD_CATEG_XMLID: PACK_TYPE_RECURRING_FEE,
    PACK_TYPE_SHARE_RECURRING_FEE_PROD_CATEG_XMLID: PACK_TYPE_SHARE_RECURRING_FEE,
    PACK_TYPE_PLATFORM_PROD_CATEG_XMLID: PACK_TYPE_PLATFORM,
    PACK_TYPE_SELFCONSUMPTION_PROD_CATEG_XMLID: PACK_TYPE_SELFCONSUMPTION,
}
