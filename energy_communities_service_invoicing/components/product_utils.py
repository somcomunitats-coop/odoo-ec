from typing import List

from odoo.addons.component.core import Component
from odoo.addons.product.models.product_template import ProductTemplate

from ..schemas import (
    BaseProductCreationData,
    PackProductCreationData,
    ProductCreationResult,
    ServiceProductCreationData,
)


class ProductUtils(Component):
    _inherit = "product.utils"

    def create_products(
        self,
        pack_product_creation_data: PackProductCreationData = False,
        service_product_creation_data_list: List[ServiceProductCreationData] = False,
    ) -> ProductCreationResult:
        pack_product_template = False
        service_product_template_list = []
        # PACK PRODUCT
        if pack_product_creation_data:
            pack_product_template = self._create_pack_product(
                pack_product_creation_data
            )
        # SERVICE PRODUCTS
        if service_product_creation_data_list:
            for service_product_creation_data in service_product_creation_data_list:
                service_product_template_list.append(
                    self._create_base_product(
                        BaseProductCreationData(
                            company_id=service_product_creation_data.company_id,
                            categ_id=service_product_creation_data.categ_id,
                            name=service_product_creation_data.name,
                            description_sale=service_product_creation_data.description_sale,
                            list_price=service_product_creation_data.list_price,
                            taxes_id=service_product_creation_data.taxes_id,
                        )
                    )
                )
        return ProductCreationResult(
            pack_product_template=pack_product_template,
            service_product_template_list=service_product_template_list,
        )

    def _create_pack_product(
        self, pack_product_creation_data: PackProductCreationData
    ) -> ProductTemplate:
        pack_product = self._create_base_product(
            BaseProductCreationData(
                company_id=pack_product_creation_data.company_id,
                categ_id=pack_product_creation_data.categ_id,
                name=pack_product_creation_data.name,
                description_sale=pack_product_creation_data.description_sale,
                list_price=pack_product_creation_data.list_price,
                taxes_id=pack_product_creation_data.taxes_id,
            )
        )
        return pack_product

    def _create_base_product(
        self, product_creation_data: BaseProductCreationData
    ) -> ProductTemplate:
        return self.env["product.template"].create(product_creation_data.dict())
