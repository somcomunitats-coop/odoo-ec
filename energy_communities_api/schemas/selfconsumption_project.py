from typing import List

from pydantic import BaseModel, Field

from odoo.addons.pydantic import utils

from .base import (
    BaseListResponse,
    BaseResponse,
    NaiveOrmModel,
    PaginationLinks,
)


class SelfConsumptionProjectInfo(NaiveOrmModel):
    class Config:
        title: "Community info"
        # used for being able to use alias on a List of this type
        allow_population_by_field_name = True

    project_code: str = Field(
        ...,
        alias="code",
        title="Project code",
        description="CAU code of the project",
    )
    project_name: str = Field(
        ...,
        alias="name",
        title="Project name",
        description="Name of the project",
    )
    energy_community_id: int = Field(
        ...,
        alias="company_id",
        title="Community Id",
        description="Id of the related community",
    )
    energy_community_name: str = Field(
        ...,
        alias="company_name",
        title="Community Name",
        description="Name of the related community",
    )
    power: float = Field(
        ...,
        title="Project power",
        description="Project power",
    )


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
    links: PaginationLinks


class ProjectInfoListResponse(BaseListResponse):
    """
    If a request claims for a collection of projects, this model will be returned
    """

    data: List[SelfConsumptionProjectInfo]
    links: PaginationLinks


class SelfConsumptionProjectMemberListResponse(BaseListResponse):
    """
    Model response when a members of a project are requested
    """

    data: List[SelfConsumptionProjectMember]
    links: PaginationLinks
