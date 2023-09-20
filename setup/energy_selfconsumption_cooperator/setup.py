import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "energy_selfconsumption": "odoo14-addon-energy-selfconsumption==14.0.2.0.0",
        }
    }
)
