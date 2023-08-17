import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "energy_project": "odoo14-addon-energy-project==14.0.1.1.3",
            "energy_communities": "odoo14-addon-energy-communities==14.0.1.1.13",
        },
    },
    
)
