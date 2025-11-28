from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from odoo.tools.translate import _

from odoo.addons.base.models.res_company import Company
from odoo.addons.product.models.product_category import ProductCategory
from odoo.addons.product.models.product_template import ProductTemplate


class SubscriptionMode(str, Enum):
    member = "member"
    company_member = "company_member"
    invited = "invited"
    company_invited = "company_invited"
    voluntary = "voluntary"


class MembershipMode(str, Enum):
    cooperator = "member"
    invited = "invited"
    voluntary = "voluntary"


class MemberTypeMode(str, Enum):
    individual = "individual"
    company = "company"


class FormTypeMode(str, Enum):
    generic = "generic"
    single = "single"


class WebsiteShareSubscriptionContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    subscription_mode: SubscriptionMode
    membership_mode: MembershipMode
    membertype_mode: MemberTypeMode
    formtype_mode: FormTypeMode
    company: Company
    product_categ: ProductCategory
    products: List[ProductTemplate]
    product: Optional[ProductTemplate]

    # product_ext_id: Optional[str] = None
    # @model_validator(mode="before")
    # @classmethod
    # def check_mode(cls, data: Any) -> Any:
    #     if not data.get("membership_mode") and not data.get("membertype_mode"):
    #         raise ValueError("Membership mode or membertype mode is required")
    #     return data

    # Avoid empty recordsets
    @field_validator("company", mode="before")
    @classmethod
    def check_company_required(cls, company: Company) -> Company:
        if not company:
            raise ValueError(_("Company must be defined"))
        return company

    @field_validator("product_categ", mode="before")
    @classmethod
    def check_product_categ_required(
        cls, product_categ: ProductCategory
    ) -> ProductCategory:
        if not product_categ:
            raise ValueError(_("Product category must be defined"))
        return product_categ

    @field_validator("products", mode="before")
    @classmethod
    def check_products_required(
        cls, products: List[ProductTemplate]
    ) -> List[ProductTemplate]:
        if not products:
            raise ValueError(_("Products must be defined"))
        return products

    @field_validator("product", mode="before")
    @classmethod
    def check_product_required(cls, product: ProductTemplate) -> ProductTemplate:
        if not product:
            raise ValueError(_("Product must be defined"))
        return product
