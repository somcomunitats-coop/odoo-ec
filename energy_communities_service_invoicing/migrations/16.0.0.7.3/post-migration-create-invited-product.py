import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.energy_communities.utils import product_utils
from odoo.addons.energy_communities_cooperator.config import (
    COOP_SHARE_PRODUCT_CATEG_REF,
)
from odoo.addons.energy_communities_service_invoicing.config import (
    COOP_ACCOUNT_REF,
)
from odoo.addons.energy_communities_service_invoicing.schemas import (
    ServiceProductCreationData,
)

logger = logging.getLogger(__name__)


def setup_components(env):
    logger.info("Setup components..")
    builder = env["component.builder"]
    # build the components of every installed addons
    comp_registry = builder._init_global_registry()
    # ensure that we load only the components of the 'installed'
    # modules, not 'to install', which means we load only the
    # dependencies of the tested addons, not the siblings or
    # children addons
    builder.build_registry(comp_registry, states=("installed",))
    # build the componenets fot energy_communities_invoicing
    builder.load_components("energy_communities_service_invoicing", comp_registry)
    env.context = dict(env.context, components_registry=comp_registry)
    return env


def migrate(cr, version):
    logger.info("energy_communities_service_invoicing")
    logger.info("Running post migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})
    env = setup_components(env)

    invited_category = env.ref(
        "energy_communities_cooperator.product_category_company_invited_share"
    )

    def _invited_product_creation_params(company):
        return ServiceProductCreationData(
            company_id=company.id,
            categ_id=invited_category.id,
            name="Registro persona/entidad invitada",
            description_sale=None,
            default_code="RI",
            list_price=0,
            taxes_id=[],
            short_name="Registro/e invitada/convidada",
            sale_ok=False,
            display_on_website=True,
            default_share_product=True,
        )

    def _invited_product_translations(invited_product):
        invited_product.with_context(lang="ca_ES").write(
            {"name": "Registre persona/entitat convidada"}
        )
        invited_product.with_context(lang="es_ES").write(
            {"name": "Registro persona/entidad invitada"}
        )
        invited_product.with_context(lang="eu_ES").write(
            {"name": "Parte hartzen duen pertsonaren/erakundearen erregistroa"}
        )

    def _get_or_create_invited_product(company):
        invited_product = env["product.template"].search(
            [("categ_id", "=", invited_category.id), ("company_id", "=", company.id)],
            limit=1,
        )
        if not invited_product:
            with product_utils(env, use_sudo=True) as product_component:
                # create company pricelist
                try:
                    product_component.create_company_pricelist(company)
                except Exception as e:
                    logger.warning(
                        "Error creating pricelist for company %s, reason: %s",
                        company.name,
                        e,
                    )
                try:
                    product_component.setup_company_product_categs(company)
                except Exception as e:
                    error_msg = f"External ID not found in the system: l10n_es.{company.id}_account_assoc_720"
                    if error_msg == str(e):
                        cooperator_account = env.ref(
                            COOP_ACCOUNT_REF.format(company.id)
                        )
                        product_component._setup_company_product_categ_accounts(
                            company,
                            COOP_SHARE_PRODUCT_CATEG_REF,
                            cooperator_account,
                            cooperator_account,
                        )
                        msg = "Error creating account %s, Fallback to %s account for company %s"
                        logger.warning(
                            msg,
                            f"l10n_es.{company.id}_account_assoc_720",
                            cooperator_account.name,
                            company.name,
                        )
                        # product_component.setup_company_product_categs(company)

                # invited product
                invited_product = product_component.create_product(
                    _invited_product_creation_params(company)
                )
                _invited_product_translations(invited_product)
                return True, invited_product
        return False, invited_product

    companies = env["res.company"].search([])
    for company in companies:
        try:
            logger.info("Creating invited product for company: %s", company.name)
            created_invited_product, invited_product = _get_or_create_invited_product(
                company
            )
        except Exception as e:
            logger.error(
                "Error creating invited product for company %s, reason: %s",
                company.name,
                e,
            )
        else:
            msg = (
                "Created product %s for company %s"
                if created_invited_product
                else "Product %s already exists in company %s"
            )
            logger.info(
                msg, invited_product.name if invited_product else "None", company.name
            )
