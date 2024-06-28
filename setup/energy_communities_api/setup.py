import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "energy_communities": "odoo14-addon-energy-communities>=14.0.8.2.1"
        },
    },
)
