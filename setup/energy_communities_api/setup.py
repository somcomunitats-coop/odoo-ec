import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "auth_jwt": "odoo-addon-auth-jwt==16.0.1.1.0.7",
            #"base_rest_auth_jwt": "odoo14-addon-base-rest-auth-jwt==14.0.1.1.0", 
            "base_rest_pydantic": "odoo-addon-base-rest-pydantic==16.0.2.0.1.2",
            "energy_communities": "odoo-addon-energy-communities==16.0.0.0.1",
            "energy_selfconsumption": "odoo-addon-energy-selfconsumption==16.0.0.0.1",
            "pydantic": "odoo-addon-pydantic==16.0.1.0.0.4",
        },
    },
)
