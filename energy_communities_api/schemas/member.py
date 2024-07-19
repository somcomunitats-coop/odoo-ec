from typing import Optional

from pydantic import BaseModel, Field

from odoo.addons.pydantic import utils


class NaiveOrmModel(BaseModel):
    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class MemberInfo(BaseModel):
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
    member_number: str = Field(
        ...,
        title="Member Number",
        description="Member number assigned to this member",
    )


class MemberCommunity(NaiveOrmModel):
    class Config:
        tittle: "Member Community info"
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
