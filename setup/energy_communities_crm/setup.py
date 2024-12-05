import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        "depends_override": {
            "crm_metadata": "odoo-addon-crm-metadata==16.0.0.1.0",
            "crm_metadata_rest_api": "odoo-addon-crm-metadata-rest-api==16.0.0.1.0",
            "crm_rest_api": "odoo-addon-crm-rest-api==16.0.0.1.0",
            "energy_communities": "odoo-addon-energy-communities>=16.0.0.0.1",
        },
    },
)
