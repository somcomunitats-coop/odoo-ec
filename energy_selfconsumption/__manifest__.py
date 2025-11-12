# Copyright 2024 Coopdevs Treball SCCL & Som Energia SCCL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Energy Self-consumption Projects",
    "summary": "Comprehensive management of energy self-consumption projects and communities",
    "description": """
Energy Self-consumption Projects Management
==========================================

This module provides comprehensive functionality for managing energy self-consumption
projects and communities, including:

**Core Features:**
* Self-consumption project creation and management
* Participant inscription and enrollment processes
* Supply point management and validation
* Distribution table creation and coefficient calculation
* Contract generation and invoicing automation
* IBAN and mandate management for participants

**Key Capabilities:**
* **Project Management**: Complete lifecycle management of self-consumption projects
* **Participant Management**: Registration, validation, and state management of participants
* **Distribution Management**: Automated calculation and management of energy distribution coefficients
* **Financial Integration**: Seamless integration with accounting and invoicing systems
* **Data Import/Export**: Bulk operations for participant data and distribution tables
* **Compliance**: Spanish energy regulation compliance and validation

**Technical Features:**
* Advanced CSV import/export capabilities with encoding detection
* Robust validation systems for Spanish energy codes (CUPS, IBAN, NIF)
* Multi-step wizards for complex operations
* Comprehensive error handling and logging
* Real-time validation and feedback
* Integration with energy communities framework

**User Experience:**
* Intuitive web forms for public inscriptions
* Multi-step wizards for complex operations
* Comprehensive validation with descriptive error messages
* Preview capabilities for critical operations
* Detailed logging and audit trails

This module is specifically designed for Spanish energy communities and cooperatives
managing collective self-consumption projects under Spanish energy regulations.
    """,
    "author": "Som IT SCCL & Som Energia SCCL",
    "website": "https://git.coopdevs.org/coopdevs/comunitats-energetiques/odoo-ce",
    "version": "16.0.0.5.13",
    "category": "Energy Management",
    "license": "AGPL-3",
    "maintainers": ["coopdevs", "som-energia"],
    # Technical information
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 100,
    # Dependencies
    "depends": [
        # Core Odoo modules
        "base",
        "web",
        "mail",
        "account",
        # Contract management
        "contract",
        "contract_queue_job",
        "contract_mandate",
        "contract_variable_quantity",
        # Energy communities framework
        "energy_communities",
        "energy_communities_cooperator",
        "energy_project",
        "energy_communities_service_invoicing",
        # Additional functionality
        "web_m2x_options",
        "l10n_es",
        "report_csv",
    ],
    # External Python dependencies
    "external_dependencies": {
        "python": ["pandas>=2.0.3", "numpy>=1.24.4", "openupgradelib>=3.6.1"]
    },
    # Data files
    "data": [
        # Security and access control
        "security/ir_rule_data.xml",
        "security/ir.model.access.csv",
        "security/res_users_role_data.xml",
        # Master data and configuration
        "data/contract_line_qty_formula_data.xml",
        "data/custom_paper_format_views.xml",
        "data/ir_attachment_data.xml",
        "data/ir_cron.xml",
        "data/ir_sequence_data.xml",
        "data/mail_template.xml",
        "data/product_data.xml",
        "data/contract_template_data.xml",
        "data/project_type_data.xml",
        # Reports
        "reports/invoice_template.xml",
        "reports/selfconsumption_reports.xml",
        # Wizards
        "wizards/change_distribution_table_import_wizard.xml",
        "wizards/change_state_inscription_wizard_views.xml",
        "wizards/contract_generation_wizard_views.xml",
        "wizards/create_distribution_table_wizard_views.xml",
        "wizards/define_invoicing_mode_wizard_view.xml",
        "wizards/distribution_table_import_wizard_views.xml",
        "wizards/invoicing_wizard_views.xml",
        "wizards/selfconsumption_import_wizard_views.xml",
        "wizards/set_iban_inscriptions_wizard_views.xml",
        "wizards/export_csv_inscriptions_wizard_views.xml",
        # Main views
        "views/contract_views.xml",
        "views/distribution_table_views.xml",
        "views/inscription_views.xml",
        "views/selfconsumption_views.xml",
        "views/res_partner_views.xml",
        "views/supply_point_assignation_views.xml",
        "views/supply_point_views.xml",
        "views/website_inscription_data_template.xml",
    ],
    # Demo data
    "demo": [
        "demo/energy_selfconsumption_demo.xml",
    ],
    # Web assets
    "assets": {
        "web.assets_common": [
            "energy_selfconsumption/static/src/js/list_renderer.js",
            "energy_selfconsumption/static/src/views/progress_bar_template.xml",
            "energy_selfconsumption/static/src/js/progress_bar.js",
        ]
    },
    # Development and quality information
    "development_status": "Production/Stable",
    "support": "https://git.coopdevs.org/coopdevs/comunitats-energetiques/odoo-ce/issues",
    # Additional metadata
    "images": [
        "static/description/icon.png",
    ],
    # Post-installation hook (if needed)
    # "post_init_hook": "post_init_hook",
    # Uninstallation hook (if needed)
    # "uninstall_hook": "uninstall_hook",
}
