from contextlib import contextmanager
from typing import Any, List
from urllib import parse

from odoo.api import Environment
from odoo.http import HttpRequest

from odoo.addons.component.core import Component, WorkContext

from .schemas import PaginationLimits, PaginationLinks


def _get_pagination_links(
    request: HttpRequest,
    total_results: int,
    paging: PaginationLimits = None,
) -> PaginationLinks:
    if not paging:
        return PaginationLinks(
            self_=request.httprequest.url,
            next_page=None,
            previous_page=None,
        )
    page = paging.page
    page_size = paging.limit
    url_parsed = parse.urlparse(request.httprequest.url)
    next_url = (
        url_parsed._replace(
            query=parse.urlencode({"page": page + 1, "page_size": page_size})
        ).geturl()
        if paging.offset + page_size < total_results
        else None
    )
    previous_url = (
        url_parsed._replace(
            query=parse.urlencode({"page": page - 1, "page_size": page_size})
        ).geturl()
        if page > 1
        else None
    )
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


def list_response(
    request: HttpRequest,
    response_class: Any,
    collection: List[Any],
    total_results,
    paging: PaginationLimits = None,
) -> Any:
    actual_count = len(collection)
    page = 1
    if paging:
        over_size = paging.limit < len(collection)
        actual_count = paging.limit if over_size else len(collection)
        page = paging.page
    return response_class(
        data=collection,
        links=_get_pagination_links(request, total_results, paging),
        page=page,
        total_results=total_results,
        count=actual_count,
    )


@contextmanager
def api_info(
    env: Environment,
    model_name: str,
    schema_class: Any,
    community_id: int = None,
    paging: PaginationLimits = None,
) -> Component:
    if community_id:
        company = env["res.company"].browse(int(community_id))
        backend = env["api.info.backend"].with_company(company).browse(1)
    else:
        backend = env["api.info.backend"].browse(1)

    work = WorkContext(
        model_name,
        community_id=community_id,
        collection=backend,
        schema_class=schema_class,
        paging=paging,
    )
    yield work.component(usage="api.info")
