from typing import Any

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
    return SingleProjectInfoResponse(data=object_, _links=_get_links(object_))


def make_list_response(object_: Any) -> ProjectsInfoListResponse:
    return ProjectsInfoListResponse(
        total_results=len(object_),
        count=len(object_),
        data=object_,
        _links=_get_pagination(object_),
    )
