from collections import namedtuple

from ..schemas import (
    PackProductCreationData,
    ServiceProductCreationData,
    ServiceProductExistingData,
)

PackProductDataTestingCase = namedtuple(
    "PackProductDataTestingCase", list(PackProductCreationData.model_fields.keys())
)

ServiceProductCreationDataTestingCase = namedtuple(
    "ServiceProductCreationDataTestingCase",
    list(ServiceProductCreationData.model_fields.keys()),
)

ServiceProductExistingDataTestingCase = namedtuple(
    "ServiceProductExistingDataTestingCase",
    list(ServiceProductExistingData.model_fields.keys()),
)

ProductUtilsTestingCase = namedtuple(
    "ProductUtilsTestingCase", ["pack_product_case", "service_product_case"]
)

_PACK_PRODUCT_TESTING_CASES = {
    "fixed_prepaid_recurring_fee_pack": PackProductDataTestingCase(
        "Community 2",
        "energy_communities.product_category_recurring_fee_pack",
        "Recurring fee pack test 1",
        "Recurring fee pack test 1 long description",
        "TP1",
        11,
        ["l10n_es.4_account_tax_template_s_iva21s"],
        "fixed",
        "pre-paid",
        False,
        False,
        "yearly",
        "22",
        "03",
    ),
    "fixed_prepaid_share_recurring_fee_pack": PackProductDataTestingCase(
        "Community 2",
        "energy_communities.product_category_share_recurring_fee_pack",
        "Recurring fee share pack test 1",
        "Recurring fee share pack test 1 long description",
        "TP2",
        11,
        ["l10n_es.4_account_tax_template_s_iva21s"],
        "fixed",
        "pre-paid",
        False,
        False,
        "yearly",
        "22",
        "03",
    ),
    "interval_prepaid_platform_pack": PackProductDataTestingCase(
        "Platform Company",
        "energy_communities_service_invoicing.product_category_platform_pack",
        "Platform pack test 1",
        "Platform pack test 1 long description",
        "TP3",
        0,
        ["l10n_es.4_account_tax_template_s_iva21s"],
        "interval",
        "pre-paid",
        2,
        "quarterly",
        False,
        False,
        False,
    ),
    "interval_prepaid_selfconsumption_pack": PackProductDataTestingCase(
        "Community 1",
        "energy_selfconsumption.product_category_selfconsumption_pack",
        "Selfconsumption pack test 1",
        "Selfconsumption pack test 1 long description",
        "TP4",
        0,
        ["l10n_es.4_account_tax_template_s_iva21s"],
        "interval",
        "pre-paid",
        2,
        "quarterly",
        False,
        False,
        False,
    ),
}

_SERVICE_PRODUCT_TESTING_CASES = {
    "recurring_fee_services": [
        ServiceProductCreationDataTestingCase(
            "Community 2",
            "energy_communities.product_category_recurring_fee_service",
            "Recurring fee service test 1",
            "Recurring fee service test 1 long description",
            "TS1",
            18,
            ["l10n_es.4_account_tax_template_s_iva21s"],
            "fixed",
            1,
            False,
        ),
        ServiceProductCreationDataTestingCase(
            "Community 2",
            "energy_communities.product_category_recurring_fee_service",
            "Recurring fee service test 2",
            "Recurring fee service test 2 long description",
            False,
            17,
            ["l10n_es.4_account_tax_template_s_iva21s"],
            "fixed",
            3,
            False,
        ),
    ],
    "platform_services": [
        ServiceProductCreationDataTestingCase(
            "Platform Company",
            "energy_communities_service_invoicing.product_category_platform_service",
            "Platform service test 1",
            "Platform service test 1 long description",
            "TS3",
            3,
            ["l10n_es.4_account_tax_template_s_iva21s"],
            "variable",
            False,
            "energy_communities_service_invoicing.active_community_members_formula",
        ),
        ServiceProductExistingDataTestingCase(
            "energy_communities_service_invoicing.demo_platform_service_product_template",
            15,
            "fixed",
            2,
            False,
        ),
    ],
    "selfconsumption_services": [
        ServiceProductCreationDataTestingCase(
            "Community 1",
            "energy_selfconsumption.product_category_selfconsumption_service",
            "Selfconsumption service test 1",
            "Selfconsumption service test 1 long description",
            "TS4",
            8,
            ["l10n_es.4_account_tax_template_s_iva21s"],
            "fixed",
            1,
            False,
        )
    ],
}

_PRODUCT_UTILS_TESTING_CASES = {
    "fixed_prepaid_recurring_fee": ProductUtilsTestingCase(
        _PACK_PRODUCT_TESTING_CASES["fixed_prepaid_recurring_fee_pack"],
        _SERVICE_PRODUCT_TESTING_CASES["recurring_fee_services"],
    ),
    "fixed_prepaid_share_recurring_fee": ProductUtilsTestingCase(
        _PACK_PRODUCT_TESTING_CASES["fixed_prepaid_share_recurring_fee_pack"],
        _SERVICE_PRODUCT_TESTING_CASES["recurring_fee_services"],
    ),
    "fixed_prepaid_recurring_fee_no_services": ProductUtilsTestingCase(
        _PACK_PRODUCT_TESTING_CASES["fixed_prepaid_recurring_fee_pack"],
        [],
    ),
    "interval_prepaid_platform": ProductUtilsTestingCase(
        _PACK_PRODUCT_TESTING_CASES["interval_prepaid_platform_pack"],
        _SERVICE_PRODUCT_TESTING_CASES["platform_services"],
    ),
    "interval_prepaid_selfconsumption": ProductUtilsTestingCase(
        _PACK_PRODUCT_TESTING_CASES["interval_prepaid_selfconsumption_pack"],
        _SERVICE_PRODUCT_TESTING_CASES["selfconsumption_services"],
    ),
}
