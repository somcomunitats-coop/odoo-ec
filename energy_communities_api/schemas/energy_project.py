from typing import List

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseListResponse, PaginationLinks


class EnergyPoint(BaseModel):
    model_config = ConfigDict(title="Energy Point", populate_by_name=True)
    """
    Schema for representing a energy value (production, selfconsumption...)
    """
    value: float = Field(..., title="Value", description="Value in kWh of the point")
    date_: str = Field(
        ...,
        alias="date",
        title="Date",
        description="Date (ex. 2024-06-01) of the value",
    )


class ProjectEnergyInfoListResponse(BaseListResponse):
    """
    Base response for requests that claim for energy values
    """

    data: List[EnergyPoint]
    links: PaginationLinks


class ProjectProductionInfoListResponse(ProjectEnergyInfoListResponse):
    """
    Body response for production requests
    """

    ...


class ProjectSelfconsumptionInfoListResponse(ProjectEnergyInfoListResponse):
    """
    Body response for selfconsumption requests
    """

    ...


class ProjectEnergyExportedInfoListResponse(ProjectEnergyInfoListResponse):
    """
    Body response for energy exported requests
    """

    ...


class ProjectEnergyConsumedInfoListResponse(ProjectEnergyInfoListResponse):
    """
    Body response for energy consumed requests
    """

    ...
