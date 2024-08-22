from typing import List, Optional

from pydantic import Field

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


class CommunityInfoListResponse(BaseListResponse):
    """
    When a single project is requested, this model will be returned
    """

    data: List[CommunityInfo]
    links: PaginationLinks
