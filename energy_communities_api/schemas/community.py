from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from .base import BaseListResponse, NaiveOrmModel, PaginationLinks


class CommunityInfo(NaiveOrmModel):
    class Config:
        title: "Community info"
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
        title: "Community service metrics information"
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


class UnitEnum(str, Enum):
    kwh = "kWh"
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
        ..., title="Shares", description="Shares that have a person for this service"
    )

    share_energy_production: MetricInfo = Field(
        ...,
        title="Share energy production",
        description="Shares of energy generated for a person",
    )

    selfconsumption_consumption_ratio: MetricInfo = Field(
        ...,
        title="Selfconsumption consumption ratio",
        description="Ratio of energy consumend",
    )

    selfconsumption_surplus_ratio: MetricInfo = Field(
        ...,
        title="Selfconsumption surplus ratio",
        description="Ratio of selfconsumption energy dumped to the net",
    )

    consumption_selfconsumption_ratio: MetricInfo = Field(
        ...,
        title="Consupmtion selfconsumption ratio",
        description="Ratio of selfconsumption energy consumed",
    )

    environment_saves: MetricInfo = Field(
        ...,
        title="Environment shaves",
        description="Amount of CO2 saved thanks to selfconsumption",
    )


class CommunityServiceInfoListResponse(BaseListResponse):
    """
    Return all community services metrics in which a member is involved.
    """

    data: List[CommunityServiceInfo]
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
