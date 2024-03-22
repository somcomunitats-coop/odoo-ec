from typing import List, Optional

from pydantic import Field

from .base import BaseListResponse, BaseResponse, Error, PaginationLinks
from .selfconsumption_project import (
    SelfConsumptionProjectInfo,
    SelfConsumptionProjectMember,
)


class ErrorResponse(BaseResponse):
    """
    When there is some error processing a request (unauthorized, body badly construncted...),
    this model will be returned
    """

    error: Error


class SingleProjectInfoResponse(BaseResponse):
    """
    When a single project is requested, this model will be returned
    """

    data: Optional[SelfConsumptionProjectInfo] = {}
    links: PaginationLinks = Field(alias="_links")


class ProjectsInfoListResponse(BaseListResponse):
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
