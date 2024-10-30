import setuptools

setuptools.setup(
    setup_requires=["setuptools-odoo"],
    odoo_addon={
        "depends_override": {
            "mass_mailing_parter": "odoo-addon-mass-mailing-partner==15.0.1.0.0.7",
            "mass_mailing_list_dynamic": "odoo-addon-mass-mailing-list-dynamic==15.0.1.0.0.9",
            # "energy_communities": "odoo14-addon-energy-communities>=14.0.9.0.0",
        }
    },
)
