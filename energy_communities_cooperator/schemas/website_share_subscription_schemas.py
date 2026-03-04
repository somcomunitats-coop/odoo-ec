from datetime import date, datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from odoo.tools.translate import _

from odoo.addons.base.models.res_company import Company
from odoo.addons.base.models.res_country import Country
from odoo.addons.base_iban.models.res_partner_bank import validate_iban
from odoo.addons.product.models.product_category import ProductCategory
from odoo.addons.product.models.product_template import ProductTemplate

from ..config import (
    COMTEXT_VALIDATION_ERROR_NO_CATEGORY,
    COMTEXT_VALIDATION_ERROR_NO_COMPANY,
    COMTEXT_VALIDATION_ERROR_NO_PRODUCT,
    CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
    CONTEXT_VALIDATION_ERROR_TITLE,
)
from ..exceptions import ControllerContextValidationError, URLValidationError


class SubscriptionMode(str, Enum):
    member = "member"
    member_associations = "member_associations"
    company_member = "company_member"
    company_member_associations = "company_member_associations"
    invited = "invited"
    company_invited = "company_invited"
    voluntary = "voluntary"


class MemberShipMode(str, Enum):
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
    transfer = "transfer"


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
    payment_method: PaymentMethodOption
    iban: Optional[str] = None
    conditions_payment: Optional[bool] = None
    privacy_policy: Optional[bool] = None
    generic_rules: Optional[bool] = None
    internal_rules: Optional[bool] = None
    financial_risk: Optional[bool] = None

    @model_validator(mode="before")
    def empty_strings_to_none(cls, data):
        for k, v in data.items():
            if v == "":
                data[k] = None
        return data

    @model_validator(mode="after")
    def check_iban_sepa(self) -> Self:
        if self.payment_method == PaymentMethodOption.sepa:
            try:
                validate_iban(self.iban.replace(" ", ""))
            except:
                raise ValueError(_("Invalid iban format"))
        return self


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
    payment_method: PaymentMethodOption
    iban: Optional[str] = None
    conditions_payment: Optional[bool] = None
    privacy_policy: Optional[bool] = None

    @model_validator(mode="before")
    def empty_strings_to_none(cls, data):
        for k, v in data.items():
            if v == "":
                data[k] = None
        return data


class SubscriptionRequestCreationParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    source: str
    email: EmailStr
    firstname: str
    lastname: str
    gender: GenderOption
    birthdate: date
    phone: str
    lang: str
    vat: str
    address: str
    city: str
    zip_code: str
    country_id: Country
    share_product_id: ProductTemplate
    ordered_parts: int
    company_id: Company
    company_name: Optional[str] = None
    company_email: Optional[EmailStr] = None
    contact_person_function: Optional[str] = None
    iban: Optional[str] = None
    mandate_approved: Optional[bool] = None
    data_policy_approved: Optional[bool] = None
    generic_rules_approved: Optional[bool] = None
    internal_rules_approved: Optional[bool] = None
    financial_risk_approved: Optional[bool] = None

    # Not necesary for SR creation
    membership_mode: MemberShipMode = Field(exclude=True)
    membertype_mode: MemberTypeMode = Field(exclude=True)
    product_categ: ProductCategory = Field(exclude=True)

    # Avoid empty recordsets
    @field_validator(
        "company_id", "product_categ", "share_product_id", "country_id", mode="before"
    )
    @classmethod
    def check_records_required(cls, record: Any) -> Any:
        if not record:
            raise ValueError(_("records_required"))
        return record

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

    @field_serializer("share_product_id", mode="plain")
    def serialize_share_product_id(self, share_product_id) -> int:
        return share_product_id.product_variant_id.id

    @field_serializer("gender", mode="plain")
    def serialize_gender(self, gender) -> str:
        return gender.value

    @field_serializer("country_id", mode="plain")
    def serialize_gender(self, country_id) -> int:
        return country_id.id

    @field_serializer("company_id", mode="plain")
    def serialize_gender(self, company_id) -> int:
        return company_id.id


class WebsiteShareSubscriptionContext(BaseModel):
    # TODO: this class oveloads two problems. For one hand, validate if in the URL
    # are present all parameters and the values are resources in our system
    # On the other hand, also validates if that values are correct
    # This beaviour should be fixed in furthers developments
    model_config = ConfigDict(arbitrary_types_allowed=True)
    subscription_mode: SubscriptionMode
    membership_mode: MemberShipMode
    membertype_mode: MemberTypeMode
    formtype_mode: FormTypeMode
    company: Company
    product_categ: ProductCategory
    products: List[ProductTemplate]
    product: Optional[ProductTemplate]

    @field_validator("company", mode="before")
    @classmethod
    def check_company_required(cls, company: Company) -> Company:
        if not company:
            raise URLValidationError(
                CONTEXT_VALIDATION_ERROR_TITLE,
                COMTEXT_VALIDATION_ERROR_NO_COMPANY,
            )
        return company

    @field_validator("product_categ", mode="before")
    @classmethod
    def check_product_categ_required(
        cls, product_categ: ProductCategory
    ) -> ProductCategory:
        if not product_categ:
            raise URLValidationError(
                CONTEXT_VALIDATION_ERROR_TITLE,
                COMTEXT_VALIDATION_ERROR_NO_CATEGORY,
            )
        return product_categ

    @field_validator("products", mode="before")
    @classmethod
    def check_products_required(
        cls, products: List[ProductTemplate]
    ) -> List[ProductTemplate]:
        if not products:
            raise URLValidationError(
                CONTEXT_VALIDATION_ERROR_TITLE,
                COMTEXT_VALIDATION_ERROR_NO_PRODUCT,
            )
        return products

    @field_validator("product", mode="before")
    @classmethod
    def check_product_required(cls, product: ProductTemplate) -> ProductTemplate:
        if not product:
            raise URLValidationError(
                CONTEXT_VALIDATION_ERROR_TITLE,
                COMTEXT_VALIDATION_ERROR_NO_PRODUCT,
            )
        return product

    @model_validator(mode="after")
    def check_product_company(self) -> Self:
        # Product must belong to defined company
        if self.product.company_id.id != self.company.id:
            raise ControllerContextValidationError(
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return self

    @model_validator(mode="after")
    def check_product_category(self) -> Self:
        # Product doesn't belong to defined category
        if self.product.categ_id.id != self.product_categ.id:
            raise ControllerContextValidationError(
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return self

    @model_validator(mode="after")
    def check_product_share(self) -> Self:
        # Product is not a share
        if not self.product.is_share:
            raise ControllerContextValidationError(
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return self

    @model_validator(mode="after")
    def check_product_subscription_mode_for_individuals(self) -> Self:
        # Product is not for individuals request on member,invited subscription_mode
        if (
            self.subscription_mode
            in [SubscriptionMode.member, SubscriptionMode.invited]
            and not self.product.by_individual
        ):
            raise ControllerContextValidationError(
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return self

    @model_validator(mode="after")
    def check_product_subscription_mode_for_companies(self) -> Self:
        # Product is not for companies request on member_company,invited_company subscription_mode
        if (
            self.subscription_mode
            in [SubscriptionMode.company_member, SubscriptionMode.company_invited]
            and not self.product.by_company
        ):
            raise ControllerContextValidationError(
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return self

    @model_validator(mode="after")
    def check_product_available_generic_form(self) -> Self:
        # Product not available on generic form
        if (
            self.formtype_mode == FormTypeMode.generic
            and not self.product.display_on_website
        ):
            raise ControllerContextValidationError(
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return self

    @model_validator(mode="after")
    def check_product_available_single_form(self) -> Self:
        # Product not available on single form
        if (
            self.formtype_mode == FormTypeMode.single
            and not self.product.activate_form_specific_products
        ):
            raise ControllerContextValidationError(
                CONTEXT_VALIDATION_ERROR_TITLE,
                CONTEXT_VALIDATION_ERROR_GENERIC_MESSAGE,
            )
        return self
