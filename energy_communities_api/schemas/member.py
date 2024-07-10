from extendable_pydantic import ExtendableModelMeta
from pydantic import BaseModel

from odoo.addons.pydantic import utils


class NaiveOrmModel(BaseModel):
    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class MemberInfo(NaiveOrmModel):
    email: str
    name: str
