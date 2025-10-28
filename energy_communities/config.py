from odoo import _

# General
DISPLAY_DATE_FORMAT = "%d/%m/%Y"

# Roles
PLATFORM_ADMIN = "role_platform_admin"
COORD_ADMIN = "role_coord_admin"
CE_MANAGER = "role_ce_manager"
CE_ADMIN = "role_ce_admin"

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

# Accounting
CHART_OF_ACCOUNTS_GENERAL_REF = "l10n_es.account_chart_template_pymes"
CHART_OF_ACCOUNTS_NON_PROFIT_REF = "l10n_es.account_chart_template_assoc"
CHART_OF_ACCOUNTS_GENERAL_CANARY_REF = (
    "l10n_es_igic.account_chart_template_pymes_canary"
)
CHART_OF_ACCOUNTS_NON_PROFIT_CANARY_REF = (
    "l10n_es_igic.account_chart_template_assoc_canary"
)

# State
STATE_CANARY_TF = "base.state_es_tf"
STATE_CANARY_GC = "base.state_es_gc"

# Rounding configuration
ROUNDING_CONFIGURATION_DEFAULT = {"tax_calculation_rounding_method": "round_globally"}
