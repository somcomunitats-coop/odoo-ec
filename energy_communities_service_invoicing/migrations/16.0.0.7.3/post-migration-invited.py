import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.component.core import _get_addon_name
from odoo.addons.energy_communities.utils import product_utils
from odoo.addons.energy_communities_cooperator.schemas import (
    MemberTypeMode,
    SubscriptionRequestCreationParams,
)
from odoo.addons.energy_communities_cooperator.utils import (
    subscription_request_utils,
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
                    logger.error("Error creating company pricelist: %s", e)
                product_component.setup_company_product_categs(company)
                # invited product
                invited_product = product_component.create_product(
                    _invited_product_creation_params(company)
                )
                _invited_product_translations(invited_product)
                return True, invited_product
        return False, invited_product

    def _get_invited_cooperator(partner, company):
        return (
            env["cooperative.membership"]
            .sudo()
            .search(
                [
                    ("company_id", "=", company.id),
                    ("partner_id", "=", partner.id),
                    "|",
                    ("effective_invited", "=", True),
                    ("member", "=", True),
                ]
            )
        )

    def _get_or_create_invited_cooperator(partner, company, invited_product):
        cooperator = _get_invited_cooperator(partner, company)
        if not cooperator:
            try:
                creation_params = partner.read(
                    [
                        "email",
                        "firstname",
                        "lastname",
                        "gender",
                        "birthdate",
                        "phone",
                        "lang",
                        "vat",
                        "city",
                        "country_id",
                        "birthdate",
                        "company_id",
                    ]
                )
                creation_params.update(
                    {
                        "address": partner.street,
                        "zip_code": partner.zip,
                        "ordered_parts": 1,
                        "iban": "ES2030043137684971748683",
                        "conditions_payment": True,
                        "share_product_id": invited_product,
                        "product_categ": invited_category,
                        "membertype_mode": MemberTypeMode.individual,
                        "lang": partner.lang.iso_code,
                    }
                )
                subscription_request_creation_params = (
                    SubscriptionRequestCreationParams(**creation_params)
                )
            except Exception as e:
                msg = "Error creating subscription request params with <Company={}, Partner={}>: {}"
                logger.error("Company: %s, Partner: %s", company.name, partner.name)
                raise ValueError(msg.format(company.name, partner.name, str(e)))

            try:
                # Use component to validate and create subscription request
                with subscription_request_utils(env) as component:
                    subscription_request = component.create_subscription_request(
                        subscription_request_creation_params
                    )
                    subscription_request.validate_subscription_request()
            except Exception as e:
                msg = "Error creating subscription request with <Company={}, Partner={}>: {}"
                logger.error("Company: %s, Partner: %s", company.name, partner.name)
                raise ValueError(msg.format(company.name, partner.name, str(e)))
            else:
                cooperator = _get_invited_cooperator(partner, company)
                return True, cooperator
        return False, cooperator

    companies = env["res.company"].search([])

    for company in companies:
        try:
            logger.info("Creating invited product for company: %s", company.name)
            created_invited_product, invited_product = _get_or_create_invited_product(
                company
            )
            logger.info(
                "Created invited product: Created: %s, Name: %s",
                created_invited_product,
                invited_product.name if invited_product else "None",
            )
            partners = env["res.partner"].search(
                [
                    ("company_id", "=", company.id),
                    ("no_member_autorized_in_energy_actions", "=", True),
                ]
            )
            for partner in partners:
                logger.info("Creating invited cooperator for partner: %s", partner.name)
                created_cooperator, cooperator = _get_or_create_invited_cooperator(
                    partner, company, invited_product
                )
                logger.info(
                    "Created invited cooperator: Created: %s, Name: %s",
                    created_cooperator,
                    cooperator.name,
                )
        except Exception as e:
            logger.error("Error creating invited cooperator: %s", e)
