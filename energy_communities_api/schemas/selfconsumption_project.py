from typing import List, Optional

from pydantic import ConfigDict, Field

from .base import (
    BaseListResponse,
    BaseResponse,
    NaiveOrmModel,
    PaginationLinks,
)


class SelfConsumptionProjectInfo(NaiveOrmModel):
    model_config = ConfigDict(
        title="SelfConsumption Project Info", populate_by_name=True
    )
    """
    Selfconumption project info data
    """
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


class SelfConsumptionProjectMember(NaiveOrmModel):
    model_config = ConfigDict(
        title="SelfConsumption Project Member", populate_by_name=True
    )
    """
    Selfconsumption project members info
    """
    supply_point_code: str = Field(
        ...,
        title="Supply Point Code",
        description="Supply Point code of the member",
    )

    supply_point_address: str = Field(
        ...,
        title="Supply Point Address",
        description="Supply Point address of the member",
    )

    supply_point_postalcode: str = Field(
        ...,
        title="Supply Point postalcode",
        description="Supply Point postalcode of the member",
    )

    supply_point_town: str = Field(
        ...,
        title="Supply Point Town",
        description="Supply Point town of the member",
    )

    supply_point_state: str = Field(
        ...,
        title="Supply Point State",
        description="Supply Point state of the member",
    )

    distribution_coefficient: float = Field(
        ...,
        alias="coefficient",
        title="Distribution coefficient",
        description="percentage of energy for the member",
    )

    owner_name: str = Field(
        ...,
        title="Member name",
        description="Name of the member",
    )

    owner_surnames: Optional[str] = Field(
        ...,
        title="Member surnames",
        description="Surnames of the member",
    )

    owner_vat: Optional[str] = Field(
        ...,
        title="Member VAT",
        description="VAT number of the member",
    )


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
