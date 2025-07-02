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
        0,
        ["l10n_es.4_account_tax_template_s_iva21s"],
        "interval",
        "pre-paid",
        "quaterly",
        2,
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
            17,
            ["l10n_es.4_account_tax_template_s_iva21s"],
            "fixed",
            3,
            False,
        ),
    ]
}

_PRODUCT_UTILS_TESTING_CASES = {
    "fixed_prepaid_recurring_fee": ProductUtilsTestingCase(
        _PACK_PRODUCT_TESTING_CASES["fixed_prepaid_recurring_fee_pack"],
        _SERVICE_PRODUCT_TESTING_CASES["recurring_fee_services"],
    )
}
