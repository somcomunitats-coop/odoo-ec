import logging

from odoo import SUPERUSER_ID, api
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities_cooperator.exceptions import (
    ValidationError as ECValidationError,
)
from odoo.addons.energy_communities_cooperator.schemas import (
    MemberTypeMode,
    SubscriptionRequestCreationParams,
)
from odoo.addons.energy_communities_cooperator.utils import (
    subscription_request_utils,
)

logger = logging.getLogger(__name__)

ES_ID = 68


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
    env = api.Environment(cr, 2, {})
    env = setup_components(env)

    invited_category = env.ref(
        "energy_communities_cooperator.product_category_company_invited_share"
    )
    pending_data_category = env.ref(
        "energy_communities_cooperator.invited_partner_with_pending_data"
    )

    DEFAULT_COUNTRY = env["res.country"].browse(ES_ID)

    def _mark_partner_to_pending(partner):
        partner.write({"category_id": [(4, pending_data_category.id)]})
        return True

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
                "country_id": partner.country_id or DEFAULT_COUNTRY,
                "company_id": partner.company_id,
                "birthdate": partner.birthdate_date,
                "address": partner.street,
                "zip_code": partner.zip,
                "ordered_parts": 1,
                "iban": "",
                "conditions_payment": True,
                "share_product_id": invited_product,
                "product_categ": invited_category,
                "membertype_mode": MemberTypeMode.individual,
                "lang": partner.lang,
                "source": "manual",
                "data_policy_approved": True,
                "generic_rules_approved": True,
                "internal_rules_approved": True,
                "financial_risk_approved": True,
            }
        )
        if partner.is_company:
            creation_params.update(
                {
                    "email": partner.email and partner.email.replace("@", "+1@") or "",
                    "company_email": partner.email,
                    "company_name": partner.name,
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
            except ValueError as e:
                msg = "Validation error creating subscruption request for <Company=%s, Partner=%s>: %s"
                logger.warning(msg, company.name, partner.name, str(e))
                logger.warning("Marking %s as pending", partner.name)
                _mark_partner_to_pending(partner)
                return False, None
            except Exception as e:
                msg = "Error creating subscription request params with <Company={}, Partner={}>: {}"
                logger.error("Company: %s, Partner: %s", company.name, partner.name)
                raise e
            try:
                # Use component to validate and create subscription request
                with subscription_request_utils(env, company) as component:
                    subscription_request = component.create_subscription_request(
                        subscription_request_params
                    )
                    subscription_request.skip_iban_control = True
                    subscription_request.validate_subscription_request()
            except (ValidationError, ECValidationError) as e:
                msg = "Validation error creating subscruption request for <Company=%s, Partner=%s>: %s"
                logger.warning(msg, company.name, partner.name, str(e))
                logger.warning("Marking %s as pending", partner.name)
                _mark_partner_to_pending(partner)
                return False, None
            except Exception as e:
                msg = "Error creating subscription request with <Company={}, Partner={}>: {}"
                logger.error("Company: %s, Partner: %s", company.name, partner.name)
                raise ValueError(msg.format(company.name, partner.name, str(e)))
            else:
                cooperator = _get_invited_cooperator(partner, company)
                return True, cooperator
        return False, cooperator

    def _get_invited_product(company):
        return (
            env["product.template"]
            .with_company(company.id)
            .search(
                [
                    ("categ_id", "=", invited_category.id),
                    ("company_id", "=", company.id),
                    ("list_price", "=", 0),
                ],
                limit=1,
            )
        )

    def _get_partners_to_migrate(company):
        return (
            env["res.partner"]
            .with_company(company.id)
            .search(
                [
                    ("no_member_autorized_in_energy_actions", "=", True),
                    ("id", "!=", company.partner_id.id),
                    # ("category_id", "not in", [pending_data_category.id]),
                ]
            )
        )

    companies = env["res.company"].search([("id", "=", 233)])
    for company in companies:
        logger.info(">>>>>>>> Starting migration for company %s", company.name)
        invited_product = _get_invited_product(company)
        if not (partners := _get_partners_to_migrate(company)):
            logger.info("Any invited partner to migrate")
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
                if cooperator:
                    msg = "Created invited cooperator: Created: %s, Name: %s"
                    logger.info(msg, created_cooperator, cooperator.name)
                else:
                    logger.info(
                        "Partner %s has pending data to fullfill in order to create its cooperator registry",
                        partner.name,
                    )
        logger.info("========= End migration for company %s", company.name)
