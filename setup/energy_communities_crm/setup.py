import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "crm_metadata": "odoo14-addon-crm-metadata==14.0.1.0.0",
            "crm_metadata_rest_api": "odoo14-addon-crm-metadata-rest-api==14.0.1.0.2",
            "crm_rest_api": "odoo14-addon-crm-rest-api==14.0.1.0.2",
            "energy_communities": "odoo14-addon-energy-communities>=14.0.9.0.0",
        },
    }
)
