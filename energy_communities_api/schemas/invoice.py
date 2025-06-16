from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from odoo.addons.account.models.account_move import PAYMENT_STATE_SELECTION

from .base import BaseResponse, NaiveOrmModel, PaginationLinks

PaymentState = Enum(
    "PaymentState", ((state.upper(), state) for state, _ in PAYMENT_STATE_SELECTION)
)

InvoiceType = Enum(
    "InvoiceType",
    (
        [
            ("SELFCONSUMPTION", "selfconsumption"),
            ("MEMBERSHIP", "membership"),
            ("OTHER", "other"),
        ]
    ),
)


class InvoiceInfo(BaseModel):
    model_config = ConfigDict(title="Invoice Info")
    """
    Schema for invoice information
    """
    id_: int = Field(
        ...,
        alias="id",
        title="Id",
        description="Id of the Invoice",
    )

    number: str = Field(..., title="Number", description="Unique numbre of the invoice")

    service_type: InvoiceType = Field(
        ...,
        title="Service Type",
        description="Type of the service for this invoice, ex: selfconsumption, membership...",
    )

    state: PaymentState = Field(
        ..., title="State", description="State of the invoice, paid, pending..."
    )

    amount_total: float = Field(
        ..., title="Amount", description="Total amount with taxes of the invoice"
    )

    date: str = Field(
        ..., title="Invoice date", description="Date when the invoice is created"
    )

    pdf_url: HttpUrl = Field(..., title="PDF Url", description="Url for pdf download")


class InvoiceInfoListResponse(BaseResponse):
    """
    Response for invoice requests
    """

    ...
