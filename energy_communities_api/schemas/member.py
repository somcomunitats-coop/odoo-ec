from typing import Optional

from pydantic import BaseModel, Field

from odoo.addons.pydantic import utils


class NaiveOrmModel(BaseModel):
    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class MemberInfo(NaiveOrmModel):
    email: str
    name: str


class MemberCommunity(NaiveOrmModel):
    id: int
    name: str
    image: Optional[str] = Field(..., alias="logo")

    class Config:
        # used for being able to use alias on a List of this type
        allow_population_by_field_name = True
