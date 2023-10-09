import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "energy_project": "odoo14-addon-energy-project==14.0.2.0.0",
            "web_m2x_options": "odoo14-addon-web-m2x-options==14.0.1.1.1",
            "contract_invoice_start_end_dates": "odoo14-addon-contract-invoice-start-end-dates==14.0.1.0.1.dev3",
        }
    }
)
