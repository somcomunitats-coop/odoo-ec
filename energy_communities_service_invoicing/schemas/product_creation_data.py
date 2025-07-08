from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from odoo.addons.product.models.product_template import ProductTemplate


class BaseProductCreationData(BaseModel):
    company_id: Optional[int] = None
    categ_id: int
    name: str
    description_sale: Optional[str] = None
    default_code: Optional[str] = None
    list_price: float = 0.0
    taxes_id: list


class PackProductCreationData(BaseProductCreationData):
    recurring_rule_mode: str
    recurring_invoicing_type: str
    recurring_interval: Optional[int] = None
    recurring_rule_type: Optional[str] = None
    recurring_invoicing_fixed_type: Optional[str] = None
    fixed_invoicing_day: Optional[str] = None
    fixed_invoicing_month: Optional[str] = None


class ServiceProductCreationData(BaseProductCreationData):
    qty_type: Optional[str] = None
    quantity: Optional[float] = None
    qty_formula_id: Optional[int] = None


class ServiceProductExistingData(BaseModel):
    product_template_id: int
    list_price: float = 0.0
    qty_type: Optional[str] = None
    quantity: Optional[float] = None
    qty_formula_id: Optional[int] = None


class ProductCreationParams(BaseModel):
    pack: Optional[PackProductCreationData] = None
    new_services: Optional[List[ServiceProductCreationData]] = None
    existing_services: Optional[List[ServiceProductExistingData]] = None


class ProductCreationResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    pack_product_template: Optional[ProductTemplate] = None
    new_service_product_template_list: Optional[List[ProductTemplate]] = None
    existing_service_product_template_list: Optional[List[ProductTemplate]] = None
