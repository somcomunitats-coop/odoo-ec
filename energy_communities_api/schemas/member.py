from pydantic import BaseModel, Field

from odoo.addons.pydantic import utils


class NaiveOrmModel(BaseModel):
    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class MemberInfo(NaiveOrmModel):
    email: str
    name: str


class MemberCommunity(BaseModel):
    id: int
    name: str
    # image: bytes
