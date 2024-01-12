import sys

if sys.version_info >= (3, 9):
    from typing import Any
else:
    from typing_extensions import Any

from .schemas.base import FAIL, OK
from .schemas.responses import (
    ProjectsInfoListResponse,
    SingleProjectInfoResponse,
)


def _get_links(object_: Any):
    return {
        "self_": "https://foo.coop/api/energy_selfconsumption/",
        "next": None,
        "previous": None,
    }


def _get_page_info(object_: Any):
    return {"limit": 100, "offset": 0}


def _get_pagination(object_: Any):
    return dict(**_get_links(object_), **_get_page_info(object_))


def make_single_response(object_: Any) -> SingleProjectInfoResponse:
    return SingleProjectInfoResponse(state=OK, data=object_, _links=_get_links(object_))


def make_list_response(object_: Any) -> ProjectsInfoListResponse:
    return ProjectsInfoListResponse(
        state=OK, data=object_, _links=_get_pagination(object_)
    )
