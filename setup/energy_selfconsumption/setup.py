import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "energy_project": "odoo14-addon-energy-project==14.0.3.0.0",
            "web_m2x_options": "odoo14-addon-web-m2x-options==14.0.1.1.1",
            "contract_queue_job": "odoo14-addon-contract-queue-job==14.0.1.0.1.dev3",
        }
    }
)
