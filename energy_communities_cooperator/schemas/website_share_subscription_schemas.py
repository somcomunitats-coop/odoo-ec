from datetime import date, datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    field_validator,
    model_validator,
)

from odoo.tools.translate import _

from odoo.addons.base.models.res_company import Company
from odoo.addons.base.models.res_country import Country
from odoo.addons.base_iban.models.res_partner_bank import validate_iban
from odoo.addons.product.models.product_category import ProductCategory
from odoo.addons.product.models.product_template import ProductTemplate

from ..config import (
    CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
    CONTEXT_VALIDATION_ERROR_TITLE,
    STATUS_CODE_CONSISTENCY_ERROR,
    STATUS_CODE_NOT_FOUND_ERROR,
)
from ..exceptions import ControllerContextValidationError


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
    individual_company = "individual_company"


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
    email: EmailStr
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
    iban: str
    conditions_payment: bool
    privacy_policy: Optional[bool] = None

    @model_validator(mode="before")
    def empty_strings_to_none(cls, data):
        for k, v in data.items():
            if v == "":
                data[k] = None
        return data


class WebsiteShareSubscriptionSubmissionCompanyMember(
    WebsiteShareSubscriptionSubmissionBase
):
    company_name: str
    company_email: EmailStr
    contact_person_function: str


class WebsiteShareSubscriptionSubmissionVoluntary(BaseModel):
    vat: str
    email: EmailStr
    phone: str
    share_product_id: int
    ordered_parts: int
    iban: str
    conditions_payment: bool
    privacy_policy: Optional[bool] = None

    @model_validator(mode="before")
    def empty_strings_to_none(cls, data):
        for k, v in data.items():
            if v == "":
                data[k] = None
        return data


# TODO: Create this schema for subscription request params creation
class SubscriptionRequestCreationParams(WebsiteShareSubscriptionSubmissionBase):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    birthdate: date
    country_id: Country
    share_product_id: ProductTemplate
    company_id: Company
    product_categ: ProductCategory
    membertype_mode: MemberTypeMode
    lang: str
    company_name: Optional[str] = None
    company_email: Optional[EmailStr] = None
    contact_person_function: Optional[str] = None

    # Avoid empty recordsets
    @field_validator(
        "company_id", "product_categ", "share_product_id", "country_id", mode="before"
    )
    @classmethod
    def check_records_required(cls, record: Any) -> Any:
        if not record:
            raise ValueError(_("records_required"))
        return record

    @field_validator("iban", mode="before")
    @classmethod
    def check_iban_format(cls, iban: str) -> str:
        try:
            validate_iban(iban.replace(" ", ""))
        except:
            raise ValueError(_("Invalid iban format"))
        return iban

    @field_validator("birthdate", mode="before")
    @classmethod
    def check_date_format(cls, date_str: str) -> date:
        try:
            date_date = datetime.strptime(date_str, "%d/%m/%Y").date()
        except:
            try:
                date_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except:
                raise ValueError(_("Invalid date format"))
        return date_date


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
            raise ControllerContextValidationError(
                STATUS_CODE_NOT_FOUND_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return company

    # TODO: Modify this validation use strategy of unify all empty record validations
    # You must be able to pass a array of error to http_routing error template right now only accepts msg string
    @field_validator("product_categ", mode="before")
    @classmethod
    def check_product_categ_required(
        cls, product_categ: ProductCategory
    ) -> ProductCategory:
        if not product_categ:
            raise ControllerContextValidationError(
                STATUS_CODE_NOT_FOUND_ERROR,
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
            raise ControllerContextValidationError(
                STATUS_CODE_NOT_FOUND_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return products

    @field_validator("product", mode="before")
    @classmethod
    def check_product_required(cls, product: ProductTemplate) -> ProductTemplate:
        if not product:
            raise ControllerContextValidationError(
                STATUS_CODE_NOT_FOUND_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return product

    @model_validator(mode="after")
    @classmethod
    def check_data_consistency(cls, data: Any) -> Any:
        # Product must belong to defined company
        if data.product.company_id.id != data.company.id:
            raise ControllerContextValidationError(
                STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        # Product doesn't belong to defined category
        if data.product.categ_id.id != data.product_categ.id:
            raise ControllerContextValidationError(
                STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        # Product is not a share
        if not data.product.is_share:
            raise ControllerContextValidationError(
                STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        # Product is not for individuals request on member,invited subscription_mode
        if (
            data.subscription_mode
            in [SubscriptionMode.member, SubscriptionMode.invited]
            and not data.product.by_individual
        ):
            raise ControllerContextValidationError(
                STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        # Product is not for companies request on member_company,invited_company subscription_mode
        if (
            data.subscription_mode
            in [SubscriptionMode.company_member, SubscriptionMode.company_invited]
            and not data.product.by_company
        ):
            raise ControllerContextValidationError(
                STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        # Product not available on generic form
        if (
            data.formtype_mode == FormTypeMode.generic
            and not data.product.display_on_website
        ):
            raise ControllerContextValidationError(
                STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        # Product not available on single form
        if (
            data.formtype_mode == FormTypeMode.single
            and not data.product.activate_form_specific_products
        ):
            raise ControllerContextValidationError(
                STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return data
