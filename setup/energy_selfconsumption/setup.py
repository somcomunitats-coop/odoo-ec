import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        "depends_override": {
            "contract": "odoo-addon-contract==16.0.2.10.0",
            "contract_queue_job": "odoo-addon-contract-queue-job==16.0.1.0.1.5",
            "contract_mandate": "odoo-addon-contract-mandate==16.0.1.0.0.5",
            "contract_variable_quantity": "odoo-addon-contract-variable-quantity==16.0.1.1.0.3",
            "energy_communities": "odoo-addon-energy-communities>=16.0.0.0.1",
            "energy_communities_cooperator": "odoo-addon-energy-communities-cooperator>=16.0.0.0.1",
            "energy_project": "odoo-addon-energy-project==16.0.0.0.1",
            "web_m2x_options": "odoo-addon-web-m2x-options==16.0.1.1.3.1",
            "report_csv": "odoo-addon-report-csv==16.0.2.1.0",
        },
    },
)
