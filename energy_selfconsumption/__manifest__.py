{
    "name": "Energy Self-consumption Project",
    "summary": """
        Module for energetic self-consumption projects.
        """,
    "description": """
        Module for energetic self-consumption projects.
    """,
    "author": "Coopdevs Treball SCCL & Som Energia SCCL",
    "website": "https://somcomunitats.coop/",
    "category": "Customizations",
    "version": "14.0.1.1.2",
    "depends": [
        "base",
        "mail",
        "energy_project",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule_data.xml",
        "data/project_type_data.xml",
        "data/ir_sequence_data.xml",
        "views/selfconsumption_views.xml",
        "views/supply_point_views.xml",
        "views/res_partner_views.xml",
        "views/distribution_table_views.xml",
        "views/supply_point_assignation_views.xml",
    ],
}
