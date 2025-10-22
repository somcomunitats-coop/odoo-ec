import logging

from odoo import SUPERUSER_ID, _, api

_logger = logging.getLogger(__name__)

from odoo.addons.energy_communities.models.res_company import (
    _LEGAL_FORM_VALUES_NON_PROFIT,
)
from odoo.addons.energy_communities_cooperator.config import (
    COOP_SHARE_PRODUCT_CATEG_REF,
    COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF,
)
from odoo.addons.energy_communities_service_invoicing.config import (
    COOP_ACCOUNT_REF,
    COOP_ACCOUNT_REF_NONPROFIT,
    COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
    PLATFORM_ACCOUNT_REF,
    PLATFORM_ACCOUNT_REF_EXPENSE,
    PLATFORM_PACK_PRODUCT_CATEG_REF,
    PLATFORM_SERVICE_PRODUCT_CATEG_REF,
    RECURRING_FEE_ACCOUNT_REF,
    RECURRING_FEE_ACCOUNT_REF_EXPENSE,
    RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
    RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
    SELFCONSUMPTION_ACCOUNT_REF,
    SELFCONSUMPTION_ACCOUNT_REF_EXPENSE,
    SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF,
    SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF,
    SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
)


def _create_selfconsumption_journal(env, company):
    if company.hierarchy_level == "community":
        selfconsumption_product_categ = env.ref(
            "energy_selfconsumption.product_category_selfconsumption_pack"
        )
        selfconsumption_journal = env["account.journal"].search(
            [("code", "in", ["AFC", "AFCEL", "AFCES"]), ("company_id", "=", company.id)]
        )
        if not selfconsumption_journal:
            account_ref = "l10n_es.{}_account_common_7050"
            account = env.ref(account_ref.format(company.id))
            selfconsumption_journal = env["account.journal"].create(
                {
                    "name": "Autoconsumo Fotovoltaico Compartido",
                    "type": "sale",
                    "company_id": company.id,
                    "default_account_id": account.id,
                    "refund_sequence": True,
                    "code": "AFC",
                }
            )


def _setup_company_product_categs(env, company):
    _logger.info("Setting company categs: {}".format(company.name))
    _setup_company_product_categs_saleteam(env, company)
    _setup_company_product_categs_journal(env, company)
    _setup_company_product_categs_accounts(env, company)


def _setup_company_product_categs_saleteam(env, company):
    _setup_company_product_categ_saleteam(env, company, COOP_SHARE_PRODUCT_CATEG_REF)
    _setup_company_product_categ_saleteam(
        env, company, COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF
    )
    _setup_company_product_categ_saleteam(
        env, company, COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF
    )
    _setup_company_product_categ_saleteam(env, company, PLATFORM_PACK_PRODUCT_CATEG_REF)
    _setup_company_product_categ_saleteam(
        env, company, RECURRING_FEE_PACK_PRODUCT_CATEG_REF
    )
    _setup_company_product_categ_saleteam(
        env, company, SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF
    )
    _setup_company_product_categ_saleteam(
        env, company, PLATFORM_SERVICE_PRODUCT_CATEG_REF
    )
    _setup_company_product_categ_saleteam(
        env, company, RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF
    )
    _setup_company_product_categ_saleteam(
        env, company, SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF
    )
    _setup_company_product_categ_saleteam(
        env, company, SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF
    )


def _setup_company_product_categ_saleteam(env, company, categ_ref):
    default_sale_team = env["crm.team"].search(
        [
            ("company_id", "=", company.id),
            ("is_default_team", "=", True),
        ],
        limit=1,
    )
    categ_w_c = env.ref(categ_ref).with_company(company)
    if default_sale_team and not categ_w_c.service_invoicing_sale_team_id:
        categ_w_c.write(
            {
                "service_invoicing_sale_team_id": default_sale_team.id,
            }
        )


def _setup_company_product_categs_journal(env, company):
    afc_journal = env["account.journal"].search(
        [("code", "in", ["AFC", "AFCEL", "AFCES"]), ("company_id", "=", company.id)],
        limit=1,
    )
    _setup_company_product_categ_journal(
        env, company, COOP_SHARE_PRODUCT_CATEG_REF, False
    )
    _setup_company_product_categ_journal(
        env, company, COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF, False
    )
    _setup_company_product_categ_journal(
        env, company, COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF, False
    )
    _setup_company_product_categ_journal(
        env, company, PLATFORM_PACK_PRODUCT_CATEG_REF, False
    )
    _setup_company_product_categ_journal(
        env, company, RECURRING_FEE_PACK_PRODUCT_CATEG_REF, False
    )
    _setup_company_product_categ_journal(
        env, company, SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF, afc_journal
    )
    _setup_company_product_categ_journal(
        env, company, PLATFORM_SERVICE_PRODUCT_CATEG_REF, False
    )
    _setup_company_product_categ_journal(
        env, company, RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF, False
    )
    _setup_company_product_categ_journal(
        env,
        company,
        SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
        company.subscription_journal_id,
    )
    _setup_company_product_categ_journal(
        env, company, SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF, afc_journal
    )


def _setup_company_product_categ_journal(env, company, categ_ref, journal):
    categ_w_c = env.ref(categ_ref).with_company(company)
    if journal and not categ_w_c.service_invoicing_sale_journal_id:
        categ_w_c.write({"service_invoicing_sale_journal_id": journal.id})


def _setup_company_product_categs_accounts(env, company):
    # coop share product categ
    cooperator_account = False
    if company.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
        try:
            cooperator_account = env.ref(COOP_ACCOUNT_REF_NONPROFIT.format(company.id))
        except:
            pass
    if not cooperator_account:
        try:
            cooperator_account = env.ref(COOP_ACCOUNT_REF.format(company.id))
        except:
            pass
    if cooperator_account:
        _setup_company_product_categ_accounts(
            env,
            company,
            COOP_SHARE_PRODUCT_CATEG_REF,
            cooperator_account,
            cooperator_account,
        )
    else:
        _logger.warning(
            "share product categ accounts not set for company: {}".format(company.name)
        )

    # voluntary share product categ
    coop_voluntary_account = env["account.account"].search(
        [("company_id", "=", company.id), ("code", "=", "100100")]
    )
    _setup_company_product_categ_accounts(
        env,
        company,
        COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF,
        coop_voluntary_account,
        coop_voluntary_account,
    )
    # platform pack product categ
    _setup_company_product_categ_accounts(
        env,
        company,
        PLATFORM_PACK_PRODUCT_CATEG_REF,
        env.ref(PLATFORM_ACCOUNT_REF.format(company.id)),
        env.ref(PLATFORM_ACCOUNT_REF_EXPENSE.format(company.id)),
    )
    # share recurring fee pack
    if company.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
        _setup_company_product_categ_accounts(
            env,
            company,
            COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
            cooperator_account,
            cooperator_account,
        )
    else:
        _setup_company_product_categ_accounts(
            env,
            company,
            COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
        )
    # recurring fee pack
    _setup_company_product_categ_accounts(
        env,
        company,
        RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
        env.ref(RECURRING_FEE_ACCOUNT_REF.format(company.id)),
        env.ref(RECURRING_FEE_ACCOUNT_REF_EXPENSE.format(company.id)),
    )
    # selfconsumption pack
    _setup_company_product_categ_accounts(
        env,
        company,
        SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF,
        env.ref(SELFCONSUMPTION_ACCOUNT_REF.format(company.id)),
        env.ref(SELFCONSUMPTION_ACCOUNT_REF_EXPENSE.format(company.id)),
    )
    # platform service product categ
    _setup_company_product_categ_accounts(
        env,
        company,
        PLATFORM_SERVICE_PRODUCT_CATEG_REF,
        env.ref(PLATFORM_ACCOUNT_REF.format(company.id)),
        env.ref(PLATFORM_ACCOUNT_REF_EXPENSE.format(company.id)),
    )
    # share recurring fee service
    share_recurring_fee_account = False
    if company.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
        try:
            share_recurring_fee_account = env.ref(
                RECURRING_FEE_ACCOUNT_REF_NONPROFIT.format(company.id)
            )
        except:
            pass
    if not share_recurring_fee_account:
        try:
            share_recurring_fee_account = env.ref(
                RECURRING_FEE_ACCOUNT_REF.format(company.id)
            )
        except:
            pass
    if share_recurring_fee_account:
        _setup_company_product_categ_accounts(
            env,
            company,
            SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
            share_recurring_fee_account,
            share_recurring_fee_account,
        )
    else:
        _logger.warning(
            "share recurring fee service product categ accounts not set for company: {}".format(
                company.name
            )
        )
    # recurring fee service
    _setup_company_product_categ_accounts(
        env,
        company,
        RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
        env.ref(RECURRING_FEE_ACCOUNT_REF.format(company.id)),
        env.ref(RECURRING_FEE_ACCOUNT_REF_EXPENSE.format(company.id)),
    )
    # selfconsumption service
    _setup_company_product_categ_accounts(
        env,
        company,
        SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF,
        env.ref(SELFCONSUMPTION_ACCOUNT_REF.format(company.id)),
        env.ref(SELFCONSUMPTION_ACCOUNT_REF_EXPENSE.format(company.id)),
    )


def _setup_company_product_categ_accounts(
    env,
    company,
    categ_ref,
    income_account=False,
    expense_account=False,
):
    categ_w_c = env.ref(categ_ref).with_company(company)
    w_dict = {}
    if income_account and not categ_w_c.property_account_income_categ_id:
        w_dict["property_account_income_categ_id"] = income_account.id
    if expense_account and not categ_w_c.property_account_expense_categ_id:
        w_dict["property_account_expense_categ_id"] = income_account.id
    if w_dict:
        categ_w_c.write(w_dict)


# def _validate_migration(env,company):
#     try:
#         account_ref = "l10n_es.{}_account_common_7050"
#         account = env.ref(account_ref.format(company.id))
#     except Exception:
#         _logger.warning("7050 account doesn't exists for company: {}".format(company.name))
#         __import__('ipdb').set_trace()
#         raise e.message


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Starting 6.0 migration")
    companies = env["res.company"].search([("id", "!=", 241)])
    for company in companies:
        # _validate_migration(env,company)
        _create_selfconsumption_journal(env, company)
        _setup_company_product_categs(env, company)
    _logger.info("Migration completed.")
