from typing import Optional

from pydantic import BaseModel


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


class PaginationLimits(BaseModel):
    """
    When a search in a collection is paginated, this class respresents the limit of results
    and the offset for each page
    """

    limit: int
    offset: int


class PaginationLinks(BaseModel):
    """
    This class represents the links to navigate through a paginated request
    """

    self_: str
    next_page: Optional[str] = None
    previous_page: Optional[str] = None


class PaginationModel(PaginationLimits, PaginationLinks):
    """
    If a request is paginated, this model will be included to navegate through the results
    """


class Error(BaseModel):
    """
    Representation of an error in energy_selfconsumption_api
    """

    code: str
    description: str
