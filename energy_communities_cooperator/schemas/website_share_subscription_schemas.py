from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from odoo.tools.translate import _

from odoo.addons.base.models.res_company import Company
from odoo.addons.product.models.product_category import ProductCategory
from odoo.addons.product.models.product_template import ProductTemplate

from ..config import (
    CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
    CONTEXT_STATUS_CODE_NOT_FOUND_ERROR,
    CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
    CONTEXT_VALIDATION_ERROR_TITLE,
)
from ..exceptions import ContextValidationError


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

    # Avoid empty recordsets
    @field_validator("company", mode="before")
    @classmethod
    def check_company_required(cls, company: Company) -> Company:
        if not company:
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_NOT_FOUND_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return company

    @field_validator("product_categ", mode="before")
    @classmethod
    def check_product_categ_required(
        cls, product_categ: ProductCategory
    ) -> ProductCategory:
        if not product_categ:
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_NOT_FOUND_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return product_categ

    @field_validator("products", mode="before")
    @classmethod
    def check_products_required(
        cls, products: List[ProductTemplate]
    ) -> List[ProductTemplate]:
        if not products:
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_NOT_FOUND_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return products

    @field_validator("product", mode="before")
    @classmethod
    def check_product_required(cls, product: ProductTemplate) -> ProductTemplate:
        if not product:
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_NOT_FOUND_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return product

    @model_validator(mode="after")
    @classmethod
    def check_data_consistency(cls, data: Any) -> Any:
        # Product must belong to defined company
        if data.product.company_id.id != data.company.id:
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        # TODO: Missing validations
        # Product doesn't belong to defined category
        # Product is not a share
        # Product is not for individuals request on member,invited subscription_mode
        # Product is not for companies request on member_company,invited_company subscription_mode
        # Product not available on generic form
        # Product not available on single form
        return data
