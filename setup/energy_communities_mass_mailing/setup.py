import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
       "depends_override": {
           "energy_communities":  "odoo-adddon-energy-communities==14.0.8.0.1",
           "mass_mailing_parter":  "odoo-adddon-mass-mailing-parner==14.0.1.1.0",
           "mass_mailing_list_dynamic":  "odoo-adddon-mass-mailing-list-dynamic==14.0.1.0.1.dev4",
       }
    },
)
