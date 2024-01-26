from typing import Any, List

from fastapi import Request

from .dependencies import DEFAULT_PAGE_SIZE
from .schemas import (
    PaginationLimits,
    ProjectsInfoListResponse,
    SingleProjectInfoResponse,
)


def get_pagination_links(
    request: Request, actual_count: int, total_results: int, paging: PaginationLimits
) -> dict:
    page = paging.page
    page_size = paging.limit
    next_url = (
        request.url.replace_query_params(page=page + 1, page_size=page_size)._url
        if paging.offset + page_size < total_results
        else None
    )
    previous_url = (
        request.url.replace_query_params(page=page - 1, page_size=page_size)._url
        if page > 1
        else None
    )

    return {
        "self_": request.url._url,
        "next_page": next_url,
        "previous_page": previous_url,
    }


def make_single_response(object_: Any, request: Request) -> SingleProjectInfoResponse:
    return SingleProjectInfoResponse(data=object_, _links=_get_links(request))


def collection_response(
    request: Request,
    collection: List[Any],
    total_results: int,
    paging: PaginationLimits,
) -> ProjectsInfoListResponse:
    actual_count = len(collection)

    return ProjectsInfoListResponse(
        total_results=total_results,
        count=actual_count,
        page=paging.page,
        data=collection,
        _links=get_pagination_links(request, actual_count, total_results, paging),
    )
