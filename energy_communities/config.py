from odoo import _

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
PACK_TYPE_PLATFORM_PRODUCT_CATEG_XML_ID = (
    "energy_communities_service_invoicing.product_category_platform_pack"
)
PACK_TYPE_RECURRING_FEE_PRODUCT_CATEG_XML_ID = (
    "energy_communities.product_category_recurring_fee_pack"
)
PACK_TYPE_SHARE_RECURRING_FEE_PRODUCT_CATEG_XML_ID = (
    "energy_communities.product_category_share_recurring_fee_pack"
)
PACK_TYPE_SELFCONSUMPTION_PRODUCT_CATEG_XML_ID = (
    "energy_selfconsumption.product_category_selfconsumption_pack"
)

# TODO: Review where to place and how to better do the mapping
PACK_PRODUCTS_RELATION_TO_SERVICES_REFS = {
    PACK_TYPE_RECURRING_FEE_PRODUCT_CATEG_XML_ID: "energy_communities.product_category_recurring_fee_service",
    PACK_TYPE_SHARE_RECURRING_FEE_PRODUCT_CATEG_XML_ID: "energy_communities.product_category_recurring_fee_service",
    PACK_TYPE_PLATFORM_PRODUCT_CATEG_XML_ID: "energy_communities_service_invoicing.product_category_platform_service",
    PACK_TYPE_SELFCONSUMPTION_PRODUCT_CATEG_XML_ID: "energy_selfconsumption.product_category_selfconsumption_service",
}

DISPLAY_DATE_FORMAT = "%d/%m/%Y"
