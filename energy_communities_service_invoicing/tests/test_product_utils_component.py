from collections import namedtuple

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.utils import product_utils
from odoo.addons.product.models.product_template import ProductTemplate

from ..schemas import (
    BaseProductCreationData,
    PackProductCreationData,
    ProductCreationResult,
    ServiceProductCreationData,
)
from ..utils import _SHARE_PRODUCTS_CATEG_REFS

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

TestCaseData = namedtuple("TestCaseData", ["pack", "services"])

_PACK_PRODUCT_TESTING_CASES = {
    "fixed_prepaid_recurring_fee_pack": PackProductDataTestingCase(
        "Community 1",
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
    "recurring_fee_services": [
        ServiceProductDataTestingCase(
            "Community 1",
            "energy_communities.product_category_recurring_fee_service",
            "Recurring fee service test 1",
            "Recurring fee service test 1 long description",
            18,
            ["l10n_es.4_account_tax_template_s_iva21s"],
            "fixed",
            1,
            False,
        ),
        ServiceProductDataTestingCase(
            "Community 1",
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

_TESTING_CASES = {
    "fixed_prepaid_recurring_fee": ProductUtilsTestingCase(
        _PACK_PRODUCT_TESTING_CASES["fixed_prepaid_recurring_fee_pack"],
        _SERVICE_PRODUCT_TESTING_CASES["recurring_fee_services"],
    )
}


@tagged("-at_install", "post_install")
class TestProductUtilsComponent(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_pack_product_creator_component_case_1(self):
        self._pack_product_creator_component_case(
            _TESTING_CASES["fixed_prepaid_recurring_fee"]
        )

    def _pack_product_creator_component_case(self, case):
        data = self._prepare_all_case_data(case)

        # ASSERT: Products we're about to create doesn't exist
        self.assertFalse(
            bool(self.env["product.template"].search([("name", "=", data.pack.name)]))
        )
        for service_data in data.services:
            self.assertFalse(
                bool(
                    self.env["product.template"].search(
                        [("name", "=", service_data.name)]
                    )
                )
            )

        # WORKFLOW: Create products
        with product_utils(self.env) as component:
            result = component.create_products(data.pack, data.services)

        # ASSERT: Creation returns a ProductCreationResult
        self.assertIsInstance(result, ProductCreationResult)
        # ASSERT: Product Creation OK
        # for pack
        self._assert_base_product_data(result.pack_product_template, data.pack)
        self._assert_pack_product_data(result, data)
        # for services
        self.assertTrue(bool(result.service_product_template_list))
        i = 0
        for service_product_template in result.service_product_template_list:
            self._assert_base_product_data(service_product_template, data.services[i])
            i += 1
        if data.pack:
            self._assert_services_on_price_list(result.service_product_template_list)

    def _assert_base_product_data(self, product_template, test_data):
        if product_template:
            self.assertTrue(bool(product_template))
            self.assertEqual(product_template.detailed_type, "service")
            self.assertEqual(product_template.invoice_policy, "order")
            self.assertIsInstance(product_template, ProductTemplate)
            for field in BaseProductCreationData.model_fields.keys():
                if field == "company_id":
                    self.assertEqual(
                        getattr(product_template, field),
                        self.env["res.company"].browse(getattr(test_data, field)),
                    )
                elif field == "categ_id":
                    product_template_categ = getattr(product_template, field)
                    self.assertEqual(
                        product_template_categ,
                        self.env["product.category"].browse(getattr(test_data, field)),
                    )
                    if product_template_categ.data_xml_id in _SHARE_PRODUCTS_CATEG_REFS:
                        self.assertTrue(product_template.is_share)
                elif field == "taxes_id":
                    product_tax_creation_dict = []
                    for tax in getattr(product_template, field):
                        product_tax_creation_dict.append((4, tax.id))
                    self.assertEqual(
                        product_tax_creation_dict, getattr(test_data, field)
                    )
                else:
                    self.assertEqual(
                        getattr(product_template, field), getattr(test_data, field)
                    )

    def _assert_pack_product_data(self, result, data):
        pack_product = result.pack_product_template
        if pack_product:
            self.assertTrue(pack_product.is_contract)
            self.assertTrue(bool(pack_product.property_contract_template_id))
            # CONTRACT TEMPLATE
            contract_template = pack_product.property_contract_template_id
            self.assertEqual(
                contract_template.name, "[TEMPLATE] %s".format(data.pack.name)
            )
            self.assertEqual(contract_template.company_id.id, data.pack.company_id)
            self.assertEqual(
                len(contract_template.contract_line_ids), len(data.services)
            )
            i = 0
            for contract_line in contract_template.contract_line_ids:
                if data.services[i].description_sale:
                    self.assertEqual(
                        contract_line.name, data.services[i].description_sale
                    )
                else:
                    self.assertEqual(contract_line.name, data.services[i].name)
                self.assertEqual(
                    contract_line.product_id,
                    result.service_product_template_list[i].product_variant_id,
                )
                self.assertTrue(contract_line.automatic_price)
                self.assertFalse(bool(contract_line.price_unit))
                self.assertEqual(contract_line.qty_type, data.services[i].qty_type)
                if data.services[i].quantity:
                    self.assertEqual(contract_line.quantity, data.services[i].quantity)
                if data.services[i].qty_formula_id:
                    self.assertEqual(
                        contract_line.qty_formula_id.id, data.services[i].qty_formula_id
                    )
                self.assertEqual(
                    contract_line.recurring_rule_mode, data.pack.recurring_rule_mode
                )
                self.assertEqual(
                    contract_line.recurring_invoicing_type,
                    data.pack.recurring_invoicing_type,
                )
                if contract_line.recurring_rule_mode == "fixed":
                    self.assertEqual(
                        contract_line.recurring_invoicing_fixed_type,
                        data.pack.recurring_invoicing_fixed_type,
                    )
                    self.assertEqual(
                        contract_line.fixed_invoicing_day, data.pack.fixed_invoicing_day
                    )
                    self.assertEqual(
                        contract_line.fixed_invoicing_month,
                        data.pack.fixed_invoicing_month,
                    )
                if contract_line.recurring_rule_mode == "interval":
                    self.assertEqual(
                        contract_line.recurring_interval, data.pack.recurring_interval
                    )
                    self.assertEqual(
                        contract_line.recurring_rule_type, data.pack.recurring_rule_type
                    )
                i += 1

    def _assert_services_on_price_list(self, services):
        for service in services:
            if service.company_id:
                pricelist = service.company_id.pricelist_id
            else:
                pricelist = self.env.ref("product.list0")
            related_price_list_item = self.env["product.pricelist.item"].search(
                [
                    ("product_tmpl_id", "=", service.id),
                    ("fixed_price", "=", service.list_price),
                    ("pricelist_id", "=", pricelist.id),
                ]
            )
            self.assertTrue(bool(related_price_list_item))

    def _prepare_all_case_data(self, case):
        services = []
        for service_data in case.service_product_case:
            services.append(
                self._prepare_one_case_data(
                    service_data,
                    ServiceProductDataTestingCase,
                    ServiceProductCreationData,
                )
            )
        return TestCaseData(
            self._prepare_one_case_data(
                case.pack_product_case,
                PackProductDataTestingCase,
                PackProductCreationData,
            ),
            services,
        )

    def _prepare_one_case_data(
        self, product_case, testing_case_class, product_creation_data_class
    ):
        if product_case:
            params = {}
            for field in testing_case_class._fields:
                data_val = getattr(product_case, field)
                if data_val:
                    if field == "company_id":
                        params[field] = (
                            self.env["res.company"]
                            .search([("name", "=", data_val)], limit=1)
                            .id
                            if data_val
                            else None
                        )
                    elif field == "categ_id":
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
            vals.append((4, self.env.ref(ref).id))
        return vals
