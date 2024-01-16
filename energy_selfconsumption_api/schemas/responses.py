import sys

if sys.version_info >= (3, 9):
    from typing import List
else:
    from typing_extensions import List

from pydantic import Field

from .base import (
    BaseListResponse,
    BaseResponse,
    PaginationLinks,
    PaginationModel,
)
from .selfconsumption_project import (
    SelfConsumptionProjectInfo,
    SelfConsumptionProjectMember,
)


class SingleProjectInfoResponse(BaseResponse):
    """
    When a single project is requested, this model will be returned
    """

    data: SelfConsumptionProjectInfo
    links: PaginationLinks = Field(alias="_links")


class ProjectsInfoListResponse(BaseListResponse):
    """
    If a request claims for a collection of projects, this model will be returned
    """

    data: List[SelfConsumptionProjectInfo]
    links: PaginationModel = Field(alias="_links")


class ProjectMembersResponse(BaseListResponse):
    """
    Model response when a members of a project are requested
    """

    data: List[SelfConsumptionProjectMember]
    links: PaginationModel = Field(alias="_links")
