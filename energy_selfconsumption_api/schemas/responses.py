import sys

if sys.version_info >= (3, 9):
    from typing import List
else:
    from typing_extensions import List

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
    _links: PaginationLinks


class ProjectsInfoListResponse(BaseListResponse):
    """
    If a request claims for a collection of projects, this model will be returned
    """

    data: List[SelfConsumptionProjectInfo]
    _links: PaginationModel


class ProjectMembersResponse(BaseListResponse):
    """
    Model response when a members of a project are requested
    """

    data: List[SelfConsumptionProjectMember]
    _links: PaginationModel
