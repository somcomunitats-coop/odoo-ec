from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from odoo.tools.translate import _

from odoo.addons.base.models.res_company import Company
from odoo.addons.base.models.res_country import Country
from odoo.addons.base_iban.models.res_partner_bank import validate_iban
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


class GenderOption(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    not_binary = "not_binary"
    not_share = "not_share"


class PaymentMethodOption(str, Enum):
    sepa = "sepa"
    transefer = "transfer"


class WebsiteShareSubscriptionSubmissionBase(BaseModel):
    email: str
    firstname: str
    lastname: str
    gender: GenderOption
    birthdate: str
    phone: str
    lang: int
    vat: str
    address: str
    city: str
    zip_code: str
    country_id: int
    share_product_id: int
    ordered_parts: int
    privacy_policy: bool
    iban: str
    conditions_payment: bool

    # TODO: Validate email has correct format


# class WebsiteShareSubscriptionSubmissionMember(BaseModel):
# email: str
# firstname: str
# lastname: str
# gender: GenderOption
# birthdate: str
# phone: str
# lang: str
# vat: str
# address: str
# city: str
# zip_code: str
# country_id: int
# share_product_id: int
# ordered_parts: int
# privacy_policy: bool
# iban: str
# conditions_payment: bool


# TODO: Create this schema for subscription request params creation
class SubscriptionRequestCreationParams(WebsiteShareSubscriptionSubmissionBase):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    country_id: Country
    share_product_id: ProductTemplate
    company_id: Company
    product_categ: ProductCategory
    membertype_mode: MemberTypeMode
    lang: str

    # Avoid empty recordsets
    @field_validator("company_id", mode="before")
    @classmethod
    def check_company_id_required(cls, company_id: Company) -> Company:
        if not company_id:
            raise ValueError(_("company_id_required"))
        return company_id

    @field_validator("product_categ", mode="before")
    @classmethod
    def check_product_categ_required(
        cls, product_categ: ProductCategory
    ) -> ProductCategory:
        if not product_categ:
            raise ValueError(_("product_category_required"))
        return product_categ

    @field_validator("share_product_id", mode="before")
    @classmethod
    def check_share_product_id_required(
        cls, product: ProductTemplate
    ) -> ProductTemplate:
        if not product:
            raise ValueError(_("product_required"))
        return product

    @field_validator("country_id", mode="before")
    @classmethod
    def check_country_id_required(cls, country: Country) -> Country:
        if not country:
            raise ValueError(_("country_required"))
        return country

    @field_validator("iban", mode="before")
    @classmethod
    def check_iban_format(cls, iban: str) -> str:
        try:
            validate_iban(iban.replace(" ", ""))
        except:
            raise ValueError(_("Invalid format iban"))
        return iban


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
        # Product doesn't belong to defined category
        if data.product.categ_id.id != data.product_categ.id:
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        # Product is not a share
        if not data.product.is_share:
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        # Product is not for individuals request on member,invited subscription_mode
        if (
            data.subscription_mode
            in [SubscriptionMode.member, SubscriptionMode.invited]
            and not data.product.by_individual
        ):
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        # Product is not for companies request on member_company,invited_company subscription_mode
        if (
            data.subscription_mode
            in [SubscriptionMode.company_member, SubscriptionMode.company_invited]
            and not data.product.by_company
        ):
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        # Product not available on generic form
        if (
            data.formtype_mode == FormTypeMode.generic
            and not data.product.display_on_website
        ):
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        # Product not available on single form
        if (
            data.formtype_mode == FormTypeMode.single
            and not data.product.activate_form_specific_products
        ):
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return data
