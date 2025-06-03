{
    "name": "Energy Communities API/REST addon",
    "summary": """
        API/REST endpoints for energy communities
    """,
    "description": """
        This addon enables an API/REST communication with energy communities platform
    """,
    "author": "Coopdevs Treball SCCL & Som Energia SCCL & SomIT",
    "website": "https://git.coopdevs.org/coopdevs/comunitats-energetiques/odoo-ce",
    "category": "Customizations",
    "version": "16.0.0.3.1",
    "license": "AGPL-3",
    "depends": [
        "auth_jwt",
        # "base_rest_auth_jwt",
        "base_rest_pydantic",
        "base_rest",
        "component",
        "energy_communities",
        "energy_selfconsumption",
        "pydantic",
    ],
    "external_dependencies": {
        "python": [
            "pydantic==2.9.2",
            "extendable-pydantic==1.3.2",
            "email_validator==2.2.0",
        ]
    },
    "data": [
        "security/res_users_role_data.xml",
        "security/ir_rule_data.xml",
        "security/ir.model.access.csv",
        "views/auth_jwt_validator_views.xml",
    ],
    "demo": [
        "demo/energy_selfconsumption_app_demo.xml",
    ],
    "installable": True,
    "application": True,
}
