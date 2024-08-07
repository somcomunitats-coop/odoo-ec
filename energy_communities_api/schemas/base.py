from typing import Optional

from pydantic import BaseModel, Field

from odoo.addons.pydantic import utils

DEFAULT_PAGE_SIZE = 20


class NaiveOrmModel(BaseModel):
    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class BaseResponse(BaseModel):
    """
    Base response class. All rest of responses will inherit from this one
    """


class BaseListResponse(BaseResponse):
    """
    Base class for responses that return a collection of elements
    """

    total_results: int
    count: int
    page: int


# TODO: PagingParam could be none to return all elements
class PagingParam(BaseModel):
    page: Optional[int]
    page_size: Optional[int]


class PaginationLimits(BaseModel):
    """
    When a search in a collection is paginated, this class respresents the limit of results
    and the offset for each page
    """

    limit: int
    offset: int
    page: int


class BaseLinks(BaseModel):
    """
    This class represents the base links to navigate by the object
    """

    self_: str


class PaginationLinks(BaseLinks):
    """
    This class represents the links to navigate through a paginated request
    """

    next_page: Optional[str] = None
    previous_page: Optional[str] = None


class Error(BaseModel):
    """
    Representation of an error
    """

    code: str
    description: str
