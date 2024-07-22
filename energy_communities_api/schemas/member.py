from typing import Optional

from pydantic import Field

from .base import BaseResponse, NaiveOrmModel, PaginationLinks


class MemberInfo(NaiveOrmModel):
    class Config:
        title: "Member Info"

    email: str = Field(
        ...,
        title="Email",
        description="Lmail of the member",
    )
    name: str = Field(
        ...,
        title="Name",
        description="Full name of the member",
    )
    lang: str = Field(
        ...,
        title="Language",
        description="Language of the member",
    )
    # member_number: Optional[str] = Field(
    #     ...,
    #     title="Member Number",
    #     description="Member number assigned to this member",
    #     alias="logo",
    # )


class MemberInfoResponse(BaseResponse):
    """
    When a single project is requested, this model will be returned
    """

    data: MemberInfo
    links: PaginationLinks


class CommunityInfo(NaiveOrmModel):
    class Config:
        tittle: "Community info"
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
