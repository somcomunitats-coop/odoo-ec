from collections import namedtuple

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.utils import product_utils

from ..schemas import PackProductCreationData, ServiceProductCreationData

PackProductDataTestingCase = namedtuple(
    "PackProductDataTestingCase", list(PackProductCreationData.model_fields.keys())
)
ServiceProductDataTestingCase = namedtuple(
    "ServiceProductDataTestingCase",
    list(ServiceProductCreationData.model_fields.keys()),
)

ProductUtilsTestingCase = namedtuple(
    "ProductUtilsTestingCase", ["pack_product_case", "service_product_case"]
)

_PACK_PRODUCT_TESTING_CASES = {
    "fixed_prepaid_recurring_fee_pack": PackProductDataTestingCase(
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
    )
}
_SERVICE_PRODUCT_TESTING_CASES = {
    "recurring_fee_service": ServiceProductDataTestingCase(
        "energy_communities.product_category_recurring_fee_service",
        "Recurring fee service test 1",
        "Recurring fee service test 1 long description",
        18,
        ["l10n_es.4_account_tax_template_s_iva21s"],
        "fixed",
        1,
        False,
    )
}

_TESTING_CASES = {
    "fixed_prepaid_recurring_fee": ProductUtilsTestingCase(
        _PACK_PRODUCT_TESTING_CASES["fixed_prepaid_recurring_fee_pack"],
        _SERVICE_PRODUCT_TESTING_CASES["recurring_fee_service"],
    )
}


@tagged("-at_install", "post_install")
class TestProductUtilsComponent(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_pack_product_creator_wizard_case_1(self):
        self._pack_product_creator_wizard_case(
            _TESTING_CASES["fixed_prepaid_recurring_fee"]
        )

    def _pack_product_creator_wizard_case(self, case):
        data = self._prepare_all_case_data(case)
        product_category = self.env.ref(case.pack_product_case.categ_id)
        self.assertTrue(bool(product_category))

    def _prepare_all_case_data(self, case):
        return {
            "pack": self._prepare_one_case_data(
                case.pack_product_case,
                PackProductDataTestingCase,
                PackProductCreationData,
            ),
            "service": self._prepare_one_case_data(
                case.service_product_case,
                ServiceProductDataTestingCase,
                ServiceProductCreationData,
            ),
        }

    def _prepare_one_case_data(
        self, product_case, testing_case_class, product_creation_data_class
    ):
        if product_case:
            params = {}
            for field in testing_case_class._fields:
                data_val = getattr(product_case, field)
                if data_val:
                    if field == "categ_id":
                        params[field] = self.env.ref(data_val).id
                    elif field == "taxes_id":
                        params[field] = self._prepare_refs_data(data_val)
                    else:
                        params[field] = data_val
            return product_creation_data_class(**params)
        return False

    def _prepare_refs_data(self, refs):
        vals = []
        for ref in refs:
            vals.append((4, self.env.ref(ref)))
        return vals
