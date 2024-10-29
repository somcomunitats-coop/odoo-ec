import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "mass_mailing_parter":  "odoo14-addon-mass-mailing-parner==14.0.1.1.0",
            "mass_mailing_list_dynamic":  "odoo14-addon-mass-mailing-list-dynamic==14.0.1.0.1.dev4",
            "energy_communities": "odoo14-addon-energy-communities>=14.0.9.0.0",
       }
    },
)
