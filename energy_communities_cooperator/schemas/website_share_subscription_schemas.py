from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

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
    global_ = "global"
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

    # @field_validator("product_ext_id")
    # @classmethod
    # def check_product_ext_id(cls, data: Any) -> Any:
    #     if data.get("product_ext_id") and not data.get("product"):
    #         raise ValueError("Product must be provided if product_ext_id is provided")
    #     return data
