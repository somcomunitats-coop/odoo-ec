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
    "version": "14.0.2.2.0",
    "depends": [
        "base",
        "mail",
        "energy_project",
        "partner_firstname",
        "web_m2x_options",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule_data.xml",
        "data/project_type_data.xml",
        "data/ir_sequence_data.xml",
        "data/ir_attactment_data.xml",
        "data/custom_paper_format_views.xml",
        "views/selfconsumption_views.xml",
        "views/supply_point_views.xml",
        "views/res_partner_views.xml",
        "views/distribution_table_views.xml",
        "views/supply_point_assignation_views.xml",
        "wizards/selfconsumption_import_wizard_views.xml",
        "wizards/distribution_table_import_wizard_views.xml",
        "reports/selfconsumption_reports.xml",
    ],
}
