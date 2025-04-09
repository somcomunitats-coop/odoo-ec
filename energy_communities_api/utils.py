from contextlib import contextmanager
from typing import Any, List
from urllib import parse

from odoo.api import Environment
from odoo.http import HTTPRequest

from odoo.addons.component.core import Component, WorkContext

from .schemas import PaginationLimits, PaginationLinks


def _next_url(url_parsed, paging, total_results):
    params = dict(parse.parse_qsl(url_parsed.query))
    if paging.offset + paging.limit < total_results:
        params["page_size"] = paging.limit
        params["page"] = int(params.get("page", 1)) + 1
        return url_parsed._replace(query=parse.urlencode(params)).geturl()


def _previous_url(url_parsed, paging):
    params = dict(parse.parse_qsl(url_parsed.query))
    if paging.page > 1:
        params["page"] = int(params["page"]) - 1
        params["page_size"] = paging.limit
        return url_parsed._replace(query=parse.urlencode(params)).geturl()


def _get_pagination_links(
    request: HTTPRequest,
    total_results: int,
    paging: PaginationLimits = None,
) -> PaginationLinks:
    if not paging:
        return PaginationLinks(
            self_=request.httprequest.url,
            next_page=None,
            previous_page=None,
        )

    url_parsed = parse.urlparse(request.httprequest.url)
    next_url = _next_url(url_parsed, paging, total_results)
    previous_url = _previous_url(url_parsed, paging)
    return PaginationLinks(
        self_=request.httprequest.url,
        next_page=next_url,
        previous_page=previous_url,
    )


def single_response(
    request: HTTPRequest,
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
    request: HTTPRequest,
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
