import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        "depends_override": {
            # "contract_queue_job": "odoo14-addon-contract-queue-job==14.0.1.0.1.dev3",
            # "contract_mandate": "odoo14-addon-contract-mandate==14.0.1.0.1",
            # "energy_communities": "odoo14-addon-energy-communities>=14.0.9.4.0",
            # "energy_communities_cooperator": "odoo14-addon-energy-communities-cooperator>=14.0.1.0.2",
            # "energy_project": "odoo14-addon-energy-project==14.0.3.5.0",
            "contract": "odoo-addon-contract==15.0.1.11.1.1",
            "contract_variable_quantity": "odoo-addon-contract-variable-quantity==15.0.1.0.0.7",
            "web_m2x_options": "odoo-addon-web-m2x-options==15.0.1.1.1",
            "report_csv": "odoo-addon-report-csv==15.0.2.0.0.2",
        },
    },
)
