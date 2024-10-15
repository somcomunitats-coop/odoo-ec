from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field

from .base import (
    BaseListResponse,
    BaseResponse,
    NaiveOrmModel,
    PaginationLinks,
)


class CommunityInfo(NaiveOrmModel):
    class Config:
        title = "Community info"
        # used for being able to use alias on a List of this type
        allow_population_by_field_name = True

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


class CommunityServiceInfo(BaseModel):
    class Config:
        title = "Community service metrics information"
        allow_population_by_field_name = True

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

    shares: float = Field(
        ...,
        title="Shares",
        description="Percentage of shares of a member in a community service",
    )

    inscription_date: date = Field(
        ...,
        title="Inscription Date",
        description="When a member was inscribed in the community service",
    )

    inscriptions: int = Field(
        ...,
        title="Total inscriptions",
        description="Total inscriptions of a community service",
    )


class UnitEnum(str, Enum):
    wh = "Wh"
    kwh = "kWh"
    kwp = "kWp"
    kwn = "kWn"
    grco2 = "grCO2"
    percentage = "percentage"


class MetricInfo(BaseModel):
    class Config:
        title: "Metric info representation"

    value: float = Field(title="Value", description="Value of the metric")
    unit: str = Field(title="unit", description="unit for this metric, kWh, grCO2...")


class CommunityServiceMetricsInfo(BaseModel):
    class Config:
        title: "Community service metrics information"
        allow_population_by_field_name = True

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

    shares: MetricInfo = Field(
        ..., title="Shares", description="Shares that have a person for this project"
    )

    energy_shares: MetricInfo = Field(
        ...,
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
    class Config:
        title = "Energy Action information"

    name: str = Field(
        ...,
        title="name",
        description="Name of the energy action",
    )


class SocialInfo(BaseModel):
    class Config:
        title = "Social links"

    email: EmailStr = Field(..., title="Email", description="Contact email")
    web: AnyHttpUrl = Field(..., title="Web", description="Url of the website")
    twitter: Optional[AnyHttpUrl] = Field(
        None, title="X", description="Url of X profile"
    )
    instagram: Optional[AnyHttpUrl] = Field(
        None, title="Instagram", description="Url of instagram profile"
    )
    telegram: Optional[AnyHttpUrl] = Field(
        None, title="Telegram", description="Url of telegram group"
    )
    facebook: Optional[AnyHttpUrl] = Field(
        None, title="Facebook", description="Url or invitation link of whatsapp group"
    )


class EnergyCommunityInfo(BaseModel):
    class Config:
        title = "Energy Community information"
        allow_population_by_field_name = True

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

    data: CommunityServiceMetricsInfo
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
