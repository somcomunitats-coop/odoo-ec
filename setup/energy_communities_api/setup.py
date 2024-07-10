import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "auth_jwt": "odoo14-addon-auth-jwt==14.0.2.1.2",
            "base_rest_pydantic": "odoo14-addon-base-rest-pydantic==14.0.4.3.3",
            "energy_communities": "odoo14-addon-energy-communities>=14.0.8.2.1",
            "pydantic": "odoo14-addon-pydantic==14.0.1.1.2",
        },
    },
)
