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
    member_number: Optional[str] = Field(
        ...,
        title="Member Number",
        description="Member number assigned to this member",
    )


class MemberInfoResponse(BaseResponse):
    """
    When a single project is requested, this model will be returned
    """

    data: Optional[MemberInfo] = Field(
        ...,
        title="Response Data",
        description="Data returned for when asking for member info",
    )
    links: PaginationLinks
