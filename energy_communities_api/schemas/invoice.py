from typing import List

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .base import (
    BaseListResponse,
    BaseResponse,
    NaiveOrmModel,
    PaginationLinks,
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

    service_type: str = Field(
        ...,
        title="Service Type",
        description="Type of the service for this invoice, ex: selfconsumption, membership...",
    )

    state: str = Field(
        ..., title="State", description="State of the invoice, paid, pending..."
    )

    amount_total: float = Field(
        ..., title="Amount", description="Total amount with taxes of the invoice"
    )

    date: str = Field(
        ..., title="Invoice date", description="Date when the invoice is created"
    )

    pdf_url: str = Field(..., title="PDF Url", description="Url for pdf download")


class InvoicePDFInfo(BaseModel):
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

    content: str = Field(
        ..., title="Content", description="Raw pdf content of the invoice"
    )


class InvoicePDFInfoResponse(BaseResponse):
    data: InvoicePDFInfo = Field(
        None,
        title="Response data",
        description="Data returned when asking for the pdf of an invoice",
    )
    links: PaginationLinks


class InvoiceInfoResponse(BaseResponse):
    data: InvoiceInfo = Field(
        None,
        title="Response data",
        description="Data returned when asking for an invoice",
    )
    links: PaginationLinks


class InvoiceInfoListResponse(BaseListResponse):
    """
    Response for invoice requests
    """

    data: List[InvoiceInfo]
    links: PaginationLinks
