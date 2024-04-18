import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
            "fastapi": "odoo14-addon-fastapi==14.0.0.0.3",
            "energy_communities": "odoo14-addon-energy-communities==14.0.8.2.1"
        },
        "external_dependencies_override": {
            "python": {
                "httpx": "httpx==0.27.0"
            },
        },
    },
)
