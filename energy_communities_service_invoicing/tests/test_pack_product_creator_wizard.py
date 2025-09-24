from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.utils import product_utils
from odoo.addons.product.models.product_template import ProductTemplate

from ..config import ALL_PACKS, FEE_PACKS
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
class TestPackProductCreatorWizzard(
    TransactionCase, ServiceInvoicingTestingProductCreator
):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

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

    def _pack_product_creator_wizard_params(self):
        data = self._prepare_all_case_data(
            _PRODUCT_UTILS_TESTING_CASES["interval_prepaid_platform"]
        )
        wizard_params = {
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
        return wizard_params

    def test__compute_allowed_prod_categ_ids_by_user_role__platform_admin(self):
        # given a user with platform_admin_role
        platform_admin = self.ref("energy_communities.res_users_admin_plataforma_demo")
        # and all product category packs
        all_product_categories = self.env["product.category"].search(
            [
                (
                    "id",
                    "in",
                    [self.env.ref(xml_id).id for xml_id in ALL_PACKS],
                )
            ]
        )
        # and the proper params for the PackProductCreatorWizard
        wizard_params = self._pack_product_creator_wizard_params()

        # when that user create a PackProductCreatorWizard
        PackProductCreatorWizard = self.env["pack.product.creator.wizard"]
        pack_product_creator_wiz = PackProductCreatorWizard.with_user(
            user=platform_admin
        ).create(wizard_params)

        # then all packs are accesible
        self.assertEqual(
            pack_product_creator_wiz.allowed_prod_categ_ids_by_user_role,
            all_product_categories,
        )

    def test__compute_allowed_prod_categ_ids_by_user_role__coordinator_admin(self):
        # given a user with platform_admin_role
        admin_coordinator = self.ref(
            "energy_communities.res_users_admin_coordinator_1_demo"
        )
        # and the allowed product category packs for that role
        allowed_product_categories = self.env["product.category"].search(
            [
                (
                    "id",
                    "in",
                    [self.env.ref(xml_id).id for xml_id in FEE_PACKS],
                )
            ]
        )
        # and the proper params for the PackProductCreatorWizard
        wizard_params = self._pack_product_creator_wizard_params()

        # when that user create a PackProductCreatorWizard
        PackProductCreatorWizard = self.env["pack.product.creator.wizard"]
        pack_product_creator_wiz = PackProductCreatorWizard.with_user(
            user=admin_coordinator
        ).create(wizard_params)

        # then all packs are accesible
        self.assertEqual(
            pack_product_creator_wiz.allowed_prod_categ_ids_by_user_role,
            allowed_product_categories,
        )
