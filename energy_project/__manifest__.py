{
    "name": "Energy Projects",
    "summary": """
        Base module for energetic projects.
        """,
    "description": """
            Base module for energetic projects.
    """,
    "author": "Coopdevs Treball SCCL & Som Energia SCCL",
    "website": "https://coopdevs.org",
    "category": "Customizations",
    "version": "14.0.3.2.1",
    "depends": ["base", "mail", "cooperator", "account_banking_mandate"],
    "data": [
        "data/energy_project.reseller.csv",
        "data/energy_project.supplier.csv",
        "data/uom_data.xml",
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "security/ir_rule_data.xml",
        "views/inscription_views.xml",
        "views/reseller_views.xml",
        "views/supplier_views.xml",
        "views/service_views.xml",
        "views/provider_views.xml",
        "views/service_available_views.xml",
        "views/service_contract_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "demo": [
        "demo/service_demo.xml",
        "demo/provider_demo.xml",
        "demo/service_available_demo.xml",
    ],
}
