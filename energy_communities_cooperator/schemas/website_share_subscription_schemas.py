from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, field_validator, model_validator
from pydantic.dataclasses import dataclass

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


# TODO: pydantic dataclasses is not supported by models odoo, we can't use Company model,ProductCategory model and ProductTemplate model as a field in the dataclass


@dataclass
class WebsiteShareSubscriptionContext(BaseModel):
    membership_mode: MembershipMode
    membertype_mode: MemberTypeMode
    formtype_mode: FormTypeMode
    company: Company
    product_categ: ProductCategory
    product: Optional[ProductTemplate] = None
    product_ext_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def check_mode(cls, data: Any) -> Any:
        if not data.get("membership_mode") and not data.get("membertype_mode"):
            raise ValueError("Membership mode or membertype mode is required")
        return data

    @field_validator("product_ext_id")
    @classmethod
    def check_product_ext_id(cls, data: Any) -> Any:
        if data.get("product_ext_id") and not data.get("product"):
            raise ValueError("Product must be provided if product_ext_id is provided")
        return data
