import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        "depends_override": {
            "mass_mailing_parter": "odoo-addon-mass-mailing-partner==16.0.1.0.0.12",
            "mass_mailing_list_dynamic": "odoo-addon-mass-mailing-list-dynamic==16.0.1.0.0.13",
            "energy_communities": "odoo-addon-energy-communities>=16.0.0.0.1",
        }
    },
)
