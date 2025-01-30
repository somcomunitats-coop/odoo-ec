{
    "name": "Energy Self-consumption Project",
    "summary": """
        Module for energetic self-consumption projects.
        """,
    "description": """
        Module for energetic self-consumption projects.
    """,
    "author": "Coopdevs Treball SCCL & Som Energia SCCL",
    "website": "https://coopdevs.org",
    "category": "Customizations",
    "version": "16.0.0.1.3",
    "license": "AGPL-3",
    "depends": [
        "base",
        "web",
        "mail",
        "account",
        "contract",
        "contract_queue_job",
        "contract_mandate",
        "contract_variable_quantity",
        "energy_communities",
        "energy_communities_cooperator",
        "energy_project",
        "web_m2x_options",
        "l10n_es",
        "report_csv",
    ],
    "external_dependencies": {
        "python": ["pandas>=2.0.3", "numpy>=1.24.4", "openupgradelib>=3.6.1"]
    },
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule_data.xml",
        "security/res_users_role_data.xml",
        "data/project_type_data.xml",
        "data/ir_sequence_data.xml",
        "data/custom_paper_format_views.xml",
        "data/contract_line_qty_formula_data.xml",
        "data/mail_template.xml",
        "data/ir_attachment_data.xml",
        "data/ir_cron.xml",
        "views/contract_views.xml",
        "views/selfconsumption_views.xml",
        "views/supply_point_views.xml",
        "views/res_partner_views.xml",
        "views/distribution_table_views.xml",
        "views/inscription_views.xml",
        "views/supply_point_assignation_views.xml",
        "views/website_inscription_data_template.xml",
        "wizards/selfconsumption_import_wizard_views.xml",
        "wizards/distribution_table_import_wizard_views.xml",
        "wizards/contract_generation_wizard_views.xml",
        "wizards/define_invoicing_mode_wizard_view.xml",
        "wizards/invoicing_wizard_views.xml",
        "wizards/clean_supply_point_assignation_wizard_views.xml",
        "wizards/create_distribution_table_wizard_views.xml",
        "reports/selfconsumption_reports.xml",
        "reports/invoice_template.xml",
    ],
    "demo": [
        "demo/energy_selfconsumption_demo.xml",
    ],
    "assets": {
        "web.assets_common": [
            "energy_selfconsumption/static/src/js/list_renderer.js",
            "energy_selfconsumption/static/src/views/progress_bar_template.xml",
            "energy_selfconsumption/static/src/js/progress_bar.js",
        ]
    },
}
