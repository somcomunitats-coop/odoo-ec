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
    "depends": [
        "fastapi",
        "energy_selfconsumption",
    ],
    "data": [
        "data/fastapi_endpoint_data.xml",
        "data/provider_data.xml",
        "data/service_data.xml",
        "data/service_available_data.xml",
    ],
    "demo": ["demo/energy_selfconsumption_app_demo.xml"],
}
