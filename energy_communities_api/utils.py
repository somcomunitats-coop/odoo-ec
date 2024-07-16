from typing import Any, List

from odoo.http import HttpRequest

from .schemas import BaseLinks, PaginationLimits, PaginationLinks


def get_pagination_links(
    request: HttpRequest,
    total_results: int,
    paging: PaginationLimits,
) -> PaginationLinks:
    page = paging.page
    page_size = paging.limit
    # TODO: WIP Calculate urls
    next_url = None
    previous_url = None
    # next_url = (
    #     request.url.replace_query_params(page=page + 1, page_size=page_size)._url
    #     if paging.offset + page_size < total_results
    #     else None
    # )
    # previous_url = (
    #     request.url.replace_query_params(page=page - 1, page_size=page_size)._url
    #     if page > 1
    #     else None
    # )
    return PaginationLinks(
        self_=request.httprequest.url,
        next_page=next_url,
        previous_page=previous_url,
    )


def single_response(
    request: HttpRequest,
    response_class: Any,
    object_: Any,
) -> Any:
    return response_class(
        data=object_,
        links=PaginationLinks(
            self_=request.httprequest.url,
            next_page=None,
            previous_page=None,
        ),
    )


def collection_response(
    request: HttpRequest,
    response_class: Any,
    collection: List[Any],
    paging: PaginationLimits,
) -> Any:
    actual_count = len(collection)
    return response_class(
        data=collection,
        links=get_pagination_links(request, actual_count, paging),
    )
