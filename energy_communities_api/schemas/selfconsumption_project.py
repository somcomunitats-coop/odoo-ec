from typing import List

from pydantic import BaseModel, Field

from .base import (
    BaseListResponse,
    BaseResponse,
    NaiveOrmModel,
    PaginationLinks,
)


class SelfConsumptionProjectInfo(BaseModel):
    project_code: str
    project_name: str
    energy_community_id: int
    energy_community_name: str
    power: float


class SelfConsumptionProjectMember(BaseModel):
    supply_point_code: str
    supply_point_address: str
    supply_point_postalcode: str
    supply_point_town: str
    supply_point_state: str
    distribution_coefficient: float
    owner_name: str
    owner_surnames: str
    owner_vat: str


class ProjectInfoResponse(BaseResponse):
    """
    When a single project is requested, this model will be returned
    """

    data: SelfConsumptionProjectInfo
    links: PaginationLinks = Field(alias="_links")


class ProjectInfoListResponse(BaseListResponse):
    """
    If a request claims for a collection of projects, this model will be returned
    """

    data: List[SelfConsumptionProjectInfo]
    links: PaginationLinks = Field(alias="_links")


class ProjectMembersResponse(BaseListResponse):
    """
    Model response when a members of a project are requested
    """

    data: List[SelfConsumptionProjectMember]
    links: PaginationLinks = Field(alias="_links")
