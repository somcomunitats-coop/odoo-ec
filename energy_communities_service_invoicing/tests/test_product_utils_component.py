from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.utils import product_utils
from odoo.addons.product.models.product_template import ProductTemplate

from ..schemas import (
    BaseProductCreationData,
    PackProductCreationData,
    ProductCreationParams,
    ProductCreationResult,
    ServiceProductCreationData,
    ServiceProductExistingData,
)
from ..utils import _SHARE_PRODUCTS_CATEG_REFS
from .testing_cases import (
    _PRODUCT_UTILS_TESTING_CASES,
    PackProductDataTestingCase,
    ServiceProductCreationDataTestingCase,
    ServiceProductExistingDataTestingCase,
)


@tagged("-at_install", "post_install")
class TestProductUtilsComponent(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_pack_product_creator_wizard_case_1(self):
        self._pack_product_creator_wizard_case(
            _PRODUCT_UTILS_TESTING_CASES["fixed_prepaid_recurring_fee"]
        )

    def test_pack_product_creator_wizard_case_2(self):
        self._pack_product_creator_wizard_case(
            _PRODUCT_UTILS_TESTING_CASES["interval_prepaid_platform"]
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
            _PRODUCT_UTILS_TESTING_CASES["fixed_prepaid_recurring_fee"]
        )

    def test_pack_product_creator_component_case_2(self):
        self._pack_product_creator_component_case(
            _PRODUCT_UTILS_TESTING_CASES["interval_prepaid_platform"]
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
        self.assertTrue(bool(result.new_service_product_template_list))
        i = 0
        for service_product_template in result.new_service_product_template_list:
            self._assert_base_product_data(
                service_product_template, data.new_services[i]
            )
            i += 1
        if data.pack:
            self._assert_services_on_price_list(
                result.new_service_product_template_list
            )

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
                    product_template_field = getattr(product_template, field)
                    if not product_template_field:
                        self.assertFalse(bool(product_template_field))
                    else:
                        self.assertEqual(
                            product_template_field, getattr(test_data, field)
                        )

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

    def _prepare_all_case_data(self, case):
        new_services = []
        existing_services = []
        for service_data in case.service_product_case:
            if isinstance(service_data, ServiceProductCreationDataTestingCase):
                new_services.append(
                    self._prepare_one_case_data(
                        service_data,
                        ServiceProductCreationDataTestingCase,
                        ServiceProductCreationData,
                    )
                )
            if isinstance(service_data, ServiceProductExistingDataTestingCase):
                existing_services.append(
                    self._prepare_one_case_data(
                        service_data,
                        ServiceProductExistingDataTestingCase,
                        ServiceProductExistingData,
                    )
                )
        return ProductCreationParams(
            pack=self._prepare_one_case_data(
                case.pack_product_case,
                PackProductDataTestingCase,
                PackProductCreationData,
            ),
            new_services=new_services,
            existing_services=existing_services,
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
                    elif field in ["categ_id", "product_template_id", "qty_formula_id"]:
                        params[field] = self.env.ref(data_val).id
                    elif field == "taxes_id":
                        params[field] = self._prepare_refs_data(data_val)
                    else:
                        if data_val:
                            params[field] = data_val
            return product_creation_data_class(**params)
        return False

    def _prepare_refs_data(self, refs):
        vals = []
        for ref in refs:
            vals.append((4, self.env.ref(ref).id))
        return vals
