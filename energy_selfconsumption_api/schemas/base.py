from pydantic import BaseModel

OK = "ok"
FAIL = "fail"


class BaseResponse(BaseModel):
    """
    Base response class. All rest of responses will inherit from this one
    """

    state: str


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
    next_page: str
    previous_page: str


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


class ErrorResponse(BaseResponse):
    """
    When there is some error processing a request (unauthorized, body badly construncted...),
    this model will be returned
    """

    error: Error
