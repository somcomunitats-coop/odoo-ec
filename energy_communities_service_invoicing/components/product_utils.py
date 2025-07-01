from typing import List

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.contract.models.contract_template import ContractTemplate
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
        # CREATE SERVICE PRODUCTS
        if service_product_creation_data_list:
            self._validate_service_configuration(service_product_creation_data_list[0])
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
        # CREATE PACK PRODUCT
        if pack_product_creation_data:
            self._apply_services_on_system_pricelist(service_product_template_list)
            pack_product_template = self._create_pack_product(
                pack_product_creation_data,
                service_product_creation_data_list,
                service_product_template_list,
            )
        return ProductCreationResult(
            pack_product_template=pack_product_template,
            service_product_template_list=service_product_template_list,
        )

    def _validate_service_configuration(
        self, service_product_creation_data: ServiceProductCreationData
    ) -> None:
        if service_product_creation_data.company_id:
            company = self.env["res.company"].browse(
                service_product_creation_data.company_id
            )
            if not company.pricelist_id:
                raise ValidationError(
                    _(
                        "Before creating services you must create and configure a Tariff model for this company"
                    )
                )

    def _apply_services_on_system_pricelist(
        self, service_product_template_list: List[ProductTemplate]
    ):
        if service_product_template_list[0].company_id:
            pricelist = service_product_template_list[0].company_id.pricelist_id
        else:
            pricelist = self.env.ref("product.list0")
        for service_product_template in service_product_template_list:
            self.env["product.pricelist.item"].create(
                {
                    "product_tmpl_id": service_product_template.id,
                    "fixed_price": service_product_template.list_price,
                    "pricelist_id": pricelist.id,
                }
            )

    def _create_pack_product(
        self,
        pack_product_creation_data: PackProductCreationData,
        service_product_creation_data_list: List[ServiceProductCreationData] = False,
        service_product_template_list: List[ProductTemplate] = False,
    ) -> ProductTemplate:
        # BASE PACK PRODUCT
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
        # CONTRACT TEMPLATE
        self._create_pack_contract_template(
            pack_product_creation_data,
            pack_product,
            service_product_creation_data_list,
            service_product_template_list,
        )
        return pack_product

    def _create_base_product(
        self, product_creation_data: BaseProductCreationData
    ) -> ProductTemplate:
        creation_dict = product_creation_data.model_dump() | {
            "detailed_type": "service",
            "invoice_policy": "order",
        }
        product = self.env["product.template"].create(creation_dict)
        self._apply_special_flags_to_product(product)
        return product

    def _apply_special_flags_to_product(self, product: ProductTemplate) -> bool:
        special_flags = {}
        if product.is_config_share:
            special_flags["is_share"] = True
        if product.is_pack:
            special_flags["is_contract"] = True
        if special_flags:
            product.write(special_flags)
            return True
        return False

    def _create_pack_contract_template(
        self,
        pack_product_creation_data: PackProductCreationData,
        pack_product: ProductTemplate,
        service_product_creation_data_list: List[ServiceProductCreationData] = False,
        service_product_template_list: List[ProductTemplate] = False,
    ) -> None:
        creation_data = {
            "name": "[TEMPLATE] {}".format(pack_product.name),
            "company_id": pack_product.company_id.id
            if pack_product.company_id
            else None,
            "contract_line_ids": [],
        }
        if service_product_creation_data_list and service_product_template_list:
            for i in range(0, len(service_product_template_list)):
                creation_data_item = {
                    "product_id": service_product_template_list[
                        i
                    ].product_variant_id.id,
                    "automatic_price": True,
                    "qty_type": service_product_creation_data_list[i].qty_type,
                    "qty_formula_id": service_product_creation_data_list[
                        i
                    ].qty_formula_id,
                    "quantity": service_product_creation_data_list[i].quantity,
                    "name": service_product_template_list[i].description_sale
                    if service_product_template_list[i].description_sale
                    else service_product_template_list[i].name,
                    "recurring_rule_mode": pack_product_creation_data.recurring_rule_mode,
                    "recurring_invoicing_type": pack_product_creation_data.recurring_invoicing_type,
                    "recurring_invoicing_fixed_type": pack_product_creation_data.recurring_invoicing_fixed_type,
                    "fixed_invoicing_day": pack_product_creation_data.fixed_invoicing_day,
                    "fixed_invoicing_month": pack_product_creation_data.fixed_invoicing_month,
                }
                if pack_product_creation_data.recurring_interval:
                    creation_data_item[
                        "recurring_interval"
                    ] = pack_product_creation_data.recurring_interval
                if pack_product_creation_data.recurring_interval:
                    creation_data_item[
                        "recurring_rule_type"
                    ] = pack_product_creation_data.recurring_rule_type
                creation_data["contract_line_ids"].append((0, 0, creation_data_item))
        contract_template = self.env["contract.template"].create(creation_data)
        pack_product.write({"property_contract_template_id": contract_template.id})
