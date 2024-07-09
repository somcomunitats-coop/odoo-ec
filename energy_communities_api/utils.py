from typing import Any, List

from odoo.http import HttpRequest

from .schemas import PaginationLimits, PaginationLinks


def get_pagination_links(
    request: HttpRequest,
    total_results: int,
    paging: PaginationLimits,
) -> PaginationLinks:
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
    return PaginationLinks(
        self_=request.url._url,
        next_page=next_url,
        previous_page=previous_url,
    )


def get_links(request: HttpRequest) -> PaginationLinks:
    return PaginationLinks(self_=request.url._url)


def single_response(
    request: HttpRequest,
    response_class: Any,
    object_: Any,
) -> Any:
    return response_class(data=object_, _links=get_links(request))


def collection_response(
    request: HttpRequest,
    response_class: Any,
    collection: List[Any],
    total_results: int,
    paging: PaginationLimits,
) -> Any:
    actual_count = len(collection)
    return response_class(
        total_results=total_results,
        count=actual_count,
        page=paging.page,
        data=collection,
        _links=get_pagination_links(request, actual_count, total_results, paging),
    )
