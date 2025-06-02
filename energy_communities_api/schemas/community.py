from enum import Enum
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, EmailStr, Field

from .base import (
    Address,
    BaseListResponse,
    BaseResponse,
    NaiveOrmModel,
    PaginationLinks,
)


class CommunityInfo(NaiveOrmModel):
    model_config = ConfigDict(title="Community info", populate_by_name=True)
    """
    Schema for representing community data (name, image...)
    """
    id: int = Field(
        ...,
        title="Id",
        description="Id of the energy community",
    )
    name: str = Field(
        ...,
        title="Name",
        description="Name of the energy community",
    )
    image: Optional[str] = Field(
        ...,
        alias="logo",
        title="Image",
        description="Image of the energy community",
    )


class CommunityServiceInfo(BaseModel, populate_by_name=True):
    model_config = ConfigDict(title="Community Service Info")
    """
    Community service metrics information
    """
    id_: int = Field(
        ...,
        alias="id",
        title="Id",
        description="Id of the community service",
    )

    type_: str = Field(
        ...,
        alias="type",
        title="Type",
        description="Type of this service, ex: fotovoltaic",
    )

    name: str = Field(
        ...,
        title="Name",
        description="Name this service, ex: Coverta Pavellò",
    )

    status: str = Field(
        ...,
        title="Status",
        description="Status of the service, ex: in_progres",
    )

    has_monitoring: bool = Field(
        ...,
        title="Has monitoring",
        description="If this service has a monitoring provider",
    )

    power: Optional[float] = Field(
        default=None,
        title="Project power",
        description="Project power",
    )

    shares: Optional[float] = Field(
        default=None,
        title="Shares",
        description="Percentage of shares of a member in a community service",
    )

    inscription_date: Optional[str] = Field(
        default=None,
        title="Inscription Date",
        description="When a member was inscribed in the community service",
    )

    open_inscriptions: Optional[bool] = Field(
        default=None,
        title="True if service has open inscriptions, false if close, None for ignore",
    )

    inscriptions_url_form: Optional[str] = Field(
        default="", title="Url of the inscription form, if inscriptions are open"
    )

    inscriptions: Optional[int] = Field(
        default=None,
        title="Total inscriptions",
        description="Total inscriptions of a community service",
    )

    address: Optional[Address] = Field(
        default=None,
        title="Address",
        description="Address where is located this service",
    )


class UnitEnum(str, Enum):
    wh = "Wh"
    kw = "kW"
    kwh = "kWh"
    kwp = "kWp"
    kwn = "kWn"
    grco2 = "grCO2"
    percentage = "percentage"


class MetricInfo(BaseModel):
    model_config = ConfigDict(title="Metric Info")
    """
    Metric info representation
    """
    value: float = Field(title="Value", description="Value of the metric")
    unit: str = Field(title="unit", description="unit for this metric, kWh, grCO2...")


class CommunityServiceMetricsInfo(BaseModel):
    model_config = ConfigDict(
        title="Community Service Metrics Info", populate_by_name=True
    )
    """
    Community service metrics information
    """
    id_: int = Field(
        ...,
        alias="id",
        title="Id",
        description="Id of the community service",
    )

    name: str = Field(
        ...,
        title="Name",
        description="Name this service, ex: Coverta Pavellò",
    )

    type_: str = Field(
        ...,
        alias="type",
        title="Type",
        description="Type of this service, ex: fotovoltaic",
    )

    power: Optional[MetricInfo] = Field(
        None,
        title="Power",
        descriptio="Power that has a service (if is a selfconumption installation)",
    )

    shares: Optional[MetricInfo] = Field(
        None, title="Shares", description="Shares that have a person for this project"
    )

    energy_shares: Optional[MetricInfo] = Field(
        None,
        title="Energy Shares",
        description="Energy shares (distribution coefficient in kWh) that have a person for this project",
    )

    energy_consumption: MetricInfo = Field(
        ...,
        title="Eenergy consumption",
        description="Energy consumed for a person",
    )

    energy_production: MetricInfo = Field(
        ...,
        title="Eenergy production",
        description="Energy generated for a person",
    )

    selfproduction_ratio: MetricInfo = Field(
        ...,
        title="Selfproduction ratio",
        description="Ratio of selfproduced energy",
    )

    surplus_ratio: MetricInfo = Field(
        ...,
        title="Surplus ratio",
        description="Ratio of energy exported to de grid",
    )

    gridconsumption_ratio: MetricInfo = Field(
        ...,
        title="Gridconsumption ratio",
        description="Ratio of grid energy consumed",
    )

    selfconsumption_ratio: MetricInfo = Field(
        ...,
        title="Selfconsumption ratio",
        description="Ratio of selfconsumption energy consumed",
    )

    environment_saves: MetricInfo = Field(
        ...,
        title="Environment shaves",
        description="Amount of CO2 saved thanks to selfconsumption",
    )


class EnergyAction(BaseModel):
    model_config = ConfigDict(title="Energy Action", populate_by_name=True)
    """
    Energy Action information
    """
    name: str = Field(
        ...,
        title="name",
        description="Name of the energy action",
    )
    type_: str = Field(
        ..., alias="ext_id", title="Type", description="Type of the energy action"
    )
    is_active: bool = Field(
        ...,
        title="Is Active",
        description="Check that indicates if this energy action is active or not",
    )


class SocialInfo(BaseModel):
    model_config = ConfigDict(title="Social Info")
    """
    Social links representation
    """
    email: EmailStr = Field(..., title="Email", description="Contact email")
    web: str = Field(None, title="Web", description="Url of the website")
    twitter: Optional[str] = Field(None, title="X", description="Url of X profile")
    instagram: Optional[str] = Field(
        None, title="Instagram", description="Url of instagram profile"
    )
    telegram: Optional[str] = Field(
        None, title="Telegram", description="Url of telegram group"
    )
    facebook: Optional[str] = Field(
        None, title="Facebook", description="Url or invitation link of whatsapp group"
    )


class EnergyCommunityInfo(BaseModel):
    model_config = ConfigDict(title="Energy Community Info", populate_by_name=True)
    """
    Energy Community information
    """
    id: int = Field(
        ...,
        title="Id",
        description="Id of the energy community",
    )
    name: str = Field(
        ...,
        title="Name",
        description="Name of the energy community",
    )
    coordinator: str = Field(
        None, title="Coordinator", description="Coordinator for this energy community"
    )
    members: int = Field(
        ...,
        title="Members",
        description="Total of members of this community",
    )
    services: List[EnergyAction] = Field(
        ...,
        title="Services",
        description="List of services that offer this energy community",
    )
    image: Optional[str] = Field(
        ...,
        alias="logo",
        title="Image",
        description="Image of the energy community",
    )
    landing_photo: Optional[str] = Field(
        ...,
        alias="logo",
        title="Image",
        description="Image of the energy community",
    )
    social: SocialInfo = Field(
        ...,
        title="social",
        description="Set of social and contact links",
    )


class CommunityServiceInfoResponse(BaseResponse):
    """
    Response for a community service basic information in which a member is involved.
    """

    data: CommunityServiceInfo
    links: PaginationLinks


class EnergyCommunityInfoResponse(BaseResponse):
    """
    Response with the basis information about a energy community.
    """

    data: EnergyCommunityInfo
    links: PaginationLinks


class CommunityServiceInfoListResponse(BaseListResponse):
    """
    Return all community services in which a member is involved.
    """

    data: List[CommunityServiceInfo]
    links: PaginationLinks


class CommunityServiceMetricsInfoResponse(BaseResponse):
    """
    Return a community service metric information in which a member is involved.
    """

    data: Optional[CommunityServiceMetricsInfo]
    links: PaginationLinks


class CommunityServiceMetricsInfoListResponse(BaseListResponse):
    """
    Return all community services metrics in which a member is involved.
    """

    data: List[CommunityServiceMetricsInfo]
    links: PaginationLinks


class CommunityInfoListResponse(BaseListResponse):
    """
    When a single project is requested, this model will be returned
    """

    data: List[CommunityInfo]
    links: PaginationLinks
