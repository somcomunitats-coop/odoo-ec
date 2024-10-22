import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "contract": "odoo14-addon-contract==14.0.2.9.4.dev2",
            "contract_queue_job": "odoo14-addon-contract-queue-job==14.0.1.0.1.dev3",
            "contract_mandate": "odoo14-addon-contract-mandate==14.0.1.0.1",
            "contract_variable_quantity": "odoo14-addon-contract-variable-quantity==14.0.1.0.1.dev5",
            "energy_communities": "odoo14-addon-energy-communities>=14.0.9.4.0",
            "energy_communities_cooperator": "odoo14-addon-energy-communities-cooperator>=14.0.1.0.2",
            "energy_project": "odoo14-addon-energy-project==14.0.3.5.0",
            "web_m2x_options": "odoo14-addon-web-m2x-options==14.0.1.1.1",
            "report_csv": "odoo14-addon-report-csv==14.0.1.0.1.dev5",
        },
    }
)
