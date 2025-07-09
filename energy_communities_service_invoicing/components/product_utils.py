from typing import List

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.contract.models.contract_template import ContractTemplate
from odoo.addons.product.models.product_template import ProductTemplate

from ..schemas import (
    BaseProductCreationData,
    PackProductCreationData,
    ProductCreationParams,
    ProductCreationResult,
    ServiceProductCreationData,
    ServiceProductExistingData,
)


class ProductUtils(Component):
    _inherit = "product.utils"

    def create_products(
        self,
        product_creation_params: ProductCreationParams,
    ) -> ProductCreationResult:
        pack_product_template = False
        new_service_product_template_list = []
        existing_service_product_template_list = []
        # CREATE SERVICE PRODUCTS
        if product_creation_params.new_services:
            self._validate_service_configuration(
                product_creation_params.new_services[0]
            )
            for service_product_creation_data in product_creation_params.new_services:
                new_service_product_template_list.append(
                    self._create_base_product(
                        BaseProductCreationData(
                            company_id=service_product_creation_data.company_id,
                            categ_id=service_product_creation_data.categ_id,
                            name=service_product_creation_data.name,
                            description_sale=service_product_creation_data.description_sale,
                            default_code=service_product_creation_data.default_code,
                            list_price=service_product_creation_data.list_price,
                            taxes_id=service_product_creation_data.taxes_id,
                        )
                    )
                )
        # EXISTING SERVICE PRODUCTS
        if product_creation_params.existing_services:
            existing_service_product_template_list = list(
                map(
                    lambda existing_data: self.env["product.template"].browse(
                        existing_data.product_template_id
                    ),
                    product_creation_params.existing_services,
                )
            )
        # CREATE PACK PRODUCT
        if product_creation_params.pack:
            self._apply_services_on_system_pricelist(
                new_service_product_template_list
                + existing_service_product_template_list
            )
            pack_product_template = self._create_pack_product(
                product_creation_params,
                new_service_product_template_list,
                existing_service_product_template_list,
            )
        # RETURN RESULT
        return ProductCreationResult(
            pack_product_template=pack_product_template,
            new_service_product_template_list=new_service_product_template_list,
            existing_service_product_template_list=existing_service_product_template_list,
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
        if service_product_template_list:
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
        product_creation_params: ProductCreationParams,
        new_service_product_template_list: List[ProductTemplate] = False,
        existing_service_product_template_list: List[ProductTemplate] = False,
    ) -> ProductTemplate:
        # BASE PACK PRODUCT
        pack_product = self._create_base_product(
            BaseProductCreationData(
                company_id=product_creation_params.pack.company_id,
                categ_id=product_creation_params.pack.categ_id,
                name=product_creation_params.pack.name,
                description_sale=product_creation_params.pack.description_sale,
                default_code=product_creation_params.pack.default_code,
                list_price=product_creation_params.pack.list_price,
                taxes_id=product_creation_params.pack.taxes_id,
            )
        )
        # CONTRACT TEMPLATE
        self._create_pack_contract_template(
            product_creation_params,
            pack_product,
            new_service_product_template_list,
            existing_service_product_template_list,
        )
        return pack_product

    def _create_base_product(
        self, product_creation_data: BaseProductCreationData
    ) -> ProductTemplate:
        creation_dict = product_creation_data.model_dump() | {
            "detailed_type": "service",
            "invoice_policy": "order",
            "purchase_ok": False,
        }
        product = self.env["product.template"].create(creation_dict)
        self._apply_special_flags_to_product(product)
        return product

    def _apply_special_flags_to_product(self, product: ProductTemplate) -> bool:
        special_flags = {}
        if product.is_config_share:
            special_flags["is_share"] = True
            special_flags["by_company"] = True
            special_flags["by_individual"] = True
            special_flags["short_name"] = product.name
        if product.is_pack:
            special_flags["is_contract"] = True
        if special_flags:
            product.write(special_flags)
            return True
        return False

    def _create_pack_contract_template(
        self,
        product_creation_params: ProductCreationParams,
        pack_product: ProductTemplate,
        new_service_product_template_list: List[ProductTemplate] = False,
        existing_service_product_template_list: List[ProductTemplate] = False,
    ) -> None:
        creation_data = {
            "name": "[TEMPLATE] {}".format(pack_product.name),
            "company_id": pack_product.company_id.id
            if pack_product.company_id
            else None,
            "contract_line_ids": [],
        }
        creation_data[
            "contract_line_ids"
        ] += self._build_contract_template_lines_creation_data(
            product_creation_params.pack,
            product_creation_params.new_services,
            new_service_product_template_list,
        )
        creation_data[
            "contract_line_ids"
        ] += self._build_contract_template_lines_creation_data(
            product_creation_params.pack,
            product_creation_params.existing_services,
            existing_service_product_template_list,
        )
        contract_template = self.env["contract.template"].create(creation_data)
        pack_product.write({"property_contract_template_id": contract_template.id})

    def _build_contract_template_lines_creation_data(
        self,
        pack_product_data: PackProductCreationData,
        service_product_data_list: List[ServiceProductCreationData]
        | List[ServiceProductExistingData],
        service_product_template_list: List[ProductTemplate],
    ) -> list:
        lines = []
        if service_product_data_list and service_product_template_list:
            for i in range(0, len(service_product_template_list)):
                lines.append(
                    (
                        0,
                        0,
                        self._build_contract_template_line_creation_data(
                            pack_product_data,
                            service_product_data_list[i],
                            service_product_template_list[i],
                        ),
                    )
                )
        return lines

    def _build_contract_template_line_creation_data(
        self,
        pack_product_data: PackProductCreationData,
        service_product_data: ServiceProductCreationData | ServiceProductExistingData,
        service_product_template: ProductTemplate,
    ) -> dict:
        creation_data_item = {
            "product_id": service_product_template.product_variant_id.id,
            "automatic_price": True,
            "qty_type": service_product_data.qty_type,
            "qty_formula_id": service_product_data.qty_formula_id,
            "quantity": service_product_data.quantity,
            "name": service_product_template.description_sale
            if service_product_template.description_sale
            else service_product_template.name,
            "recurring_rule_mode": pack_product_data.recurring_rule_mode,
            "recurring_invoicing_type": pack_product_data.recurring_invoicing_type,
            "recurring_invoicing_fixed_type": pack_product_data.recurring_invoicing_fixed_type,
            "fixed_invoicing_day": pack_product_data.fixed_invoicing_day,
            "fixed_invoicing_month": pack_product_data.fixed_invoicing_month,
        }
        if pack_product_data.recurring_interval:
            creation_data_item[
                "recurring_interval"
            ] = pack_product_data.recurring_interval
        if pack_product_data.recurring_interval:
            creation_data_item[
                "recurring_rule_type"
            ] = pack_product_data.recurring_rule_type
        return creation_data_item
