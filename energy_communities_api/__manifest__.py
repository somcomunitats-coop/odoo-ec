{
    "name": "Energy self-onsumption API/REST addon",
    "summary": """
        This addon enables API/REST communication with ce_odoo for the module energy selfconsumption
    """,
    "description": """
        API/REST endpoints for selfconfumption module
    """,
    "author": "Coopdevs Treball SCCL & Som Energia SCCL & SomIT",
    "website": "https://coopdevs.org",
    "category": "Customizations",
    "version": "14.0.1.0.1",
    "depends": ["fastapi", "energy_communities"],
    "data": [
        "data/fastapi_endpoint_data.xml",
        "security/res_users_role_data.xml",
        "security/ir_rule_data.xml",
    ],
    "demo": [
        "demo/service_demo.xml",
        "demo/provider_demo.xml",
        "demo/service_available_demo.xml",
        # "demo/energy_selfconsumption_app_demo.xml",
    ],
}
