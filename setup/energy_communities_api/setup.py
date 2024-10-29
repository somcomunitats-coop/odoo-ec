import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "auth_jwt": "odoo14-addon-auth-jwt==14.0.2.1.2",
            "base_rest_auth_jwt": "odoo14-addon-base-rest-auth-jwt==14.0.1.1.0", 
            "base_rest_pydantic": "odoo14-addon-base-rest-pydantic==14.0.4.3.3",
            "energy_communities": "odoo14-addon-energy-communities>=14.0.9.4.0",
            "energy_selfconsumption": "odoo14-addon-energy-selfconsumption>=14.0.5.2.0",
            "pydantic": "odoo14-addon-pydantic==14.0.1.1.2",
        },
    },
)
