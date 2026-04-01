import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.energy_communities_cooperator.schemas import (
    MemberTypeMode,
    SubscriptionRequestCreationParams,
)
from odoo.addons.energy_communities_cooperator.utils import (
    subscription_request_utils,
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
    builder.load_components("energy_communities_cooperator", comp_registry)
    env.context = dict(env.context, components_registry=comp_registry)
    return env


def migrate(cr, version):
    logger.info("energy_communities_cooperator")
    logger.info("Running post migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})
    env = setup_components(env)

    invited_category = env.ref(
        "energy_communities_cooperator.product_category_company_invited_share"
    )

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

    def _get_subscription_request_params(partner, invited_product):
        fields = [
            "email",
            "firstname",
            "lastname",
            "gender",
            "phone",
            "lang",
            "vat",
            "city",
            "is_company",
        ]
        creation_params = partner.read(fields)[0]
        creation_params.update(
            {
                "country_id": partner.country_id,
                "company_id": partner.company_id,
                "birthdate": partner.birthdate_date,
                "address": partner.street,
                "zip_code": partner.zip,
                "ordered_parts": 1,
                "iban": "ES2030043137684971748683",
                "conditions_payment": True,
                "share_product_id": invited_product,
                "product_categ": invited_category,
                "membertype_mode": MemberTypeMode.individual,
                "lang": partner.lang,
                "source": "manual",
            }
        )
        return SubscriptionRequestCreationParams(**creation_params)

    def _get_or_create_invited_cooperator(partner, company, invited_product):
        cooperator = _get_invited_cooperator(partner, company)
        if not cooperator:
            try:
                subscription_request_params = _get_subscription_request_params(
                    partner, invited_product
                )
            except Exception as e:
                msg = "Error creating subscription request params with <Company={}, Partner={}>: {}"
                logger.error("Company: %s, Partner: %s", company.name, partner.name)
                raise ValueError(msg.format(company.name, partner.name, str(e)))
            try:
                # Use component to validate and create subscription request
                with subscription_request_utils(env) as component:
                    subscription_request = component.create_subscription_request(
                        subscription_request_params
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

    companies = env["res.company"].search([("id", "!=", 29)])
    for company in companies:
        partners = (
            env["res.partner"]
            .with_company(company.id)
            .search(
                [
                    ("no_member_autorized_in_energy_actions", "=", True),
                    ("id", "!=", company.partner_id.id),
                ]
            )
        )
        if not partners:
            logger.info("Any invited partner to migrate in company %s", company.name)
        invited_product = (
            env["product.template"]
            .with_company(company.id)
            .search([("categ_id", "=", invited_category.id), ("list_price", "=", 0)])[0]
        )
        for partner in partners:
            try:
                logger.info("Creating invited cooperator for partner %s", partner.name)
                created_cooperator, cooperator = _get_or_create_invited_cooperator(
                    partner, company, invited_product
                )
            except Exception as e:
                msg = "Error creating invited cooperator for partner %s in company %s, reason: %s"
                logger.error(msg, partner.name, company.name, e)
                raise e
            else:
                msg = ("Created invited cooperator: Created: %s, Name: %s",)
                logger.info(msg, created_cooperator, cooperator.name)
