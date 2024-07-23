from contextlib import contextmanager
from typing import Any, List, Union
from urllib import parse

from odoo.api import Environment
from odoo.http import HttpRequest

from odoo.addons.component.core import Component, WorkContext

from .schemas import PaginationLimits, PaginationLinks


def _get_pagination_links(
    request: HttpRequest,
    total_results: int,
    paging: PaginationLimits,
) -> PaginationLinks:
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
    paging: PaginationLimits,
) -> Any:
    return response_class(
        data=collection,
        links=_get_pagination_links(request, len(collection), paging),
        data_length=len(collection),
    )


@contextmanager
def api_info(
    env: Environment,
    model_name: str,
    schema_class: Any,
    record_ids: Union[List[int], int],
) -> Component:
    backend = env["api.info.backend"].browse(1)
    work = WorkContext(
        model_name, collection=backend, rec_ids=record_ids, schema_class=schema_class
    )
    yield work.component(usage="api.info")
    # with backend.work_on as recordset_worker:
    #     component = recordset_worker.component(usage="api.info")
    #     yield component
