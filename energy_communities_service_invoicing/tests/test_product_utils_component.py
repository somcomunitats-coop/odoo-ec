from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.utils import product_utils
from odoo.addons.product.models.product_template import ProductTemplate

from ..config import SHARE_PRODUCTS_CATEG_REFS
from ..schemas import (
    BaseProductCreationData,
    ProductCreationResult,
    ServiceProductCreationData,
    ServiceProductExistingData,
)
from .service_invoicing_testing_product_creator import (
    ServiceInvoicingTestingProductCreator,
)
from .testing_cases import _PRODUCT_UTILS_TESTING_CASES


@tagged("-at_install", "post_install")
class TestProductUtilsComponent(TransactionCase, ServiceInvoicingTestingProductCreator):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_pack_product_creator_wizard_case_1(self):
        self._pack_product_creator_wizard_case(
            _PRODUCT_UTILS_TESTING_CASES["interval_prepaid_platform"]
        )

    def test_pack_product_creator_wizard_case_2(self):
        self._pack_product_creator_wizard_case(
            _PRODUCT_UTILS_TESTING_CASES["fixed_prepaid_recurring_fee"]
        )

    def test_pack_product_creator_wizard_case_3(self):
        self._pack_product_creator_wizard_case(
            _PRODUCT_UTILS_TESTING_CASES["fixed_prepaid_share_recurring_fee"]
        )

    def test_pack_product_creator_wizard_case_4(self):
        self._pack_product_creator_wizard_case(
            _PRODUCT_UTILS_TESTING_CASES["fixed_prepaid_recurring_fee_no_services"]
        )

    def _pack_product_creator_wizard_case(self, case):
        data = self._prepare_all_case_data(case)
        # WORKFLOW: Create a pack creator wizard and execute create
        wizard = self.env["pack.product.creator.wizard"].create(
            {
                "company_id": data.pack.company_id,
                "pack_categ_id": data.pack.categ_id,
                "name": data.pack.name,
                "description_sale": data.pack.description_sale,
                "default_code": data.pack.default_code,
                "list_price": data.pack.list_price,
                "taxes_id": data.pack.taxes_id,
                "recurring_rule_mode": data.pack.recurring_rule_mode,
                "recurring_invoicing_type": data.pack.recurring_invoicing_type,
                "recurring_interval": data.pack.recurring_interval,
                "recurring_rule_type": data.pack.recurring_rule_type,
                "recurring_invoicing_fixed_type": data.pack.recurring_invoicing_fixed_type,
                "fixed_invoicing_day": data.pack.fixed_invoicing_day,
                "fixed_invoicing_month": data.pack.fixed_invoicing_month,
                "service_product_ids": self._get_wizard_lines_creation_data(
                    data.new_services
                )
                + self._get_wizard_lines_creation_data(data.existing_services),
            }
        )
        new_wizard_lines = self._get_wizard_lines_creation_data(data.new_services)
        existing_wizard_lines = self._get_wizard_lines_creation_data(
            data.existing_services
        )
        result = wizard._create_products()
        # ASSERT CREATION WENT OK
        self._assert_creation_ok(result, data)

    def _get_wizard_lines_creation_data(self, services_data):
        services = []
        for service_data in services_data:
            if isinstance(service_data, ServiceProductCreationData):
                line_create_dict = {
                    "type": "new",
                    "name": service_data.name,
                    "description_sale": service_data.description_sale,
                    "default_code": service_data.default_code,
                    "list_price": service_data.list_price,
                    "quantity": service_data.quantity,
                    "qty_type": service_data.qty_type,
                    "qty_formula_id": service_data.qty_formula_id,
                    "taxes_id": service_data.taxes_id,
                }
            if isinstance(service_data, ServiceProductExistingData):
                product_template = self.env["product.template"].browse(
                    service_data.product_template_id
                )
                line_create_dict = {
                    "type": "existing",
                    "existing_service_product_id": product_template.id,
                    "list_price": service_data.list_price,
                    "quantity": service_data.quantity,
                    "qty_type": service_data.qty_type,
                    "qty_formula_id": service_data.qty_formula_id,
                }
            services.append((0, 0, line_create_dict))
        return services

    def test_pack_product_creator_component_case_1(self):
        self._pack_product_creator_component_case(
            _PRODUCT_UTILS_TESTING_CASES["interval_prepaid_platform"]
        )

    def test_pack_product_creator_component_case_2(self):
        self._pack_product_creator_component_case(
            _PRODUCT_UTILS_TESTING_CASES["fixed_prepaid_recurring_fee"]
        )

    def test_pack_product_creator_component_case_3(self):
        self._pack_product_creator_component_case(
            _PRODUCT_UTILS_TESTING_CASES["fixed_prepaid_share_recurring_fee"]
        )

    def test_pack_product_creator_component_case_4(self):
        self._pack_product_creator_component_case(
            _PRODUCT_UTILS_TESTING_CASES["fixed_prepaid_recurring_fee_no_services"]
        )

    def _pack_product_creator_component_case(self, case):
        data = self._prepare_all_case_data(case)

        # ASSERT: Products we're about to create doesn't exist
        self.assertFalse(
            bool(self.env["product.template"].search([("name", "=", data.pack.name)]))
        )
        for service_data in data.new_services:
            self.assertFalse(
                bool(
                    self.env["product.template"].search(
                        [("name", "=", service_data.name)]
                    )
                )
            )

        # WORKFLOW: Create products
        with product_utils(self.env) as component:
            result = component.create_products(data)

        # ASSERT CREATION WENT OK
        self._assert_creation_ok(result, data)

    def _assert_creation_ok(self, result, data):
        # ASSERT: Creation returns a ProductCreationResult
        self.assertIsInstance(result, ProductCreationResult)
        # ASSERT: Product Creation OK
        # for pack
        self._assert_base_product_data(result.pack_product_template, data.pack)
        self._assert_pack_product_data(result, data)
        # for services
        if data.new_services:
            self._assert_services_product_data(
                result.new_service_product_template_list, data.new_services, data.pack
            )
        else:
            self.assertFalse(bool(data.new_services))
        if data.existing_services:
            self._assert_services_product_data(
                result.existing_service_product_template_list,
                data.existing_services,
                data.pack,
            )
        else:
            self.assertFalse(bool(data.existing_services))

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
                    if product_template_categ.data_xml_id in SHARE_PRODUCTS_CATEG_REFS:
                        self.assertTrue(product_template.is_share)
                        self.assertTrue(product_template.by_individual)
                        self.assertTrue(product_template.by_company)
                        self.assertEqual(
                            product_template.short_name, product_template.name
                        )
                elif field == "taxes_id":
                    product_tax_creation_dict = []
                    for tax in getattr(product_template, field):
                        product_tax_creation_dict.append((4, tax.id))
                    self.assertEqual(
                        product_tax_creation_dict, getattr(test_data, field)
                    )
                else:
                    product_template_field = getattr(product_template, field)
                    if not product_template_field:
                        self.assertFalse(bool(product_template_field))
                    else:
                        self.assertEqual(
                            product_template_field, getattr(test_data, field)
                        )

    def _assert_services_product_data(
        self, service_product_template_list, data_services, data_pack
    ):
        self.assertTrue(bool(service_product_template_list))
        i = 0
        for service_product_template in service_product_template_list:
            if isinstance(data_services[i], ServiceProductCreationData):
                self._assert_base_product_data(
                    service_product_template, data_services[i]
                )
            if isinstance(data_services[i], ServiceProductExistingData):
                self.assertEqual(
                    service_product_template.id, data_services[i].product_template_id
                )
            i += 1
        if data_pack:
            self._assert_services_on_price_list(service_product_template_list)

    def _assert_pack_product_data(self, result, data):
        pack_product = result.pack_product_template
        if pack_product:
            self.assertTrue(pack_product.is_contract)
            self.assertTrue(bool(pack_product.property_contract_template_id))
            # CONTRACT TEMPLATE
            contract_template = pack_product.property_contract_template_id
            self.assertEqual(
                contract_template.name, "[TEMPLATE] {}".format(data.pack.name)
            )
            self.assertEqual(contract_template.company_id.id, data.pack.company_id)
            self.assertEqual(
                len(contract_template.contract_line_ids),
                len(data.new_services) + len(data.existing_services),
            )
            self._assert_pack_contract_lines_consistency(
                0,
                len(data.new_services),
                data.pack,
                data.new_services,
                contract_template,
                result.new_service_product_template_list,
            )
            self._assert_pack_contract_lines_consistency(
                len(data.new_services),
                len(data.existing_services),
                data.pack,
                data.existing_services,
                contract_template,
                result.existing_service_product_template_list,
            )

    def _assert_pack_contract_lines_consistency(
        self,
        offset,
        limit,
        pack,
        services,
        contract_template,
        product_template_list,
    ):
        contract_line_pos = 0
        service_pos = 0
        for contract_line in contract_template.contract_line_ids:
            if contract_line_pos >= offset and contract_line_pos < limit:
                if services[service_pos].description_sale:
                    self.assertEqual(
                        contract_line.name, services[service_pos].description_sale
                    )
                else:
                    self.assertEqual(contract_line.name, services[service_pos].name)
                self.assertEqual(
                    contract_line.product_id,
                    product_template_list[service_pos].product_variant_id,
                )
                self.assertTrue(contract_line.automatic_price)
                self.assertFalse(bool(contract_line.price_unit))
                self.assertEqual(contract_line.qty_type, services[service_pos].qty_type)
                if services[service_pos].quantity:
                    self.assertEqual(
                        contract_line.quantity, services[service_pos].quantity
                    )
                if services[service_pos].qty_formula_id:
                    self.assertEqual(
                        contract_line.qty_formula_id.id,
                        services[service_pos].qty_formula_id,
                    )
                self.assertEqual(
                    contract_line.recurring_rule_mode, pack.recurring_rule_mode
                )
                self.assertEqual(
                    contract_line.recurring_invoicing_type,
                    pack.recurring_invoicing_type,
                )
                if contract_line.recurring_rule_mode == "fixed":
                    self.assertEqual(
                        contract_line.recurring_invoicing_fixed_type,
                        pack.recurring_invoicing_fixed_type,
                    )
                    self.assertEqual(
                        contract_line.fixed_invoicing_day, pack.fixed_invoicing_day
                    )
                    self.assertEqual(
                        contract_line.fixed_invoicing_month,
                        pack.fixed_invoicing_month,
                    )
                if contract_line.recurring_rule_mode == "interval":
                    self.assertEqual(
                        contract_line.recurring_interval, pack.recurring_interval
                    )
                    self.assertEqual(
                        contract_line.recurring_rule_type, pack.recurring_rule_type
                    )
                service_pos += 1
            contract_line_pos += 1

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
