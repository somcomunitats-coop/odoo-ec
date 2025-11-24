from collections import namedtuple
from inspect import currentframe, getouterframes
from urllib import parse

import requests

from .exceptions import RequestError, UrlNotFoundError

BackendResponse = namedtuple("BackendResponse", "content, headers, status")


class Backend:
    # Name of the authorization header
    AUTH_HEADER: str = "Authorization"

    # Provider api version if is versioned
    _api_version: str = ""

    # map betwen backend functions and provider endponts
    # _endpoints = {
    #    "project_daily_metrics": "/provider/endpoint/{project_id}",
    # }
    _endpoints: dict = {}

    # Default query params for all calls
    _default_query_params: list = []
    # query params for specific calls
    _params: dict = {}

    # Map between provider and energy_project attributes
    _field_map = {}

    def _request(self, url, **kwargs) -> BackendResponse:
        """
        Closure to manage requests to external provider apis
        """

        def _do_get(url, url_params, **kwargs) -> BackendResponse:
            response = requests.get(url, params=url_params, **kwargs)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                message = (
                    e.response.content
                    and e.response.json().get("error", str(e))
                    or str(e)
                )
                raise RequestError(
                    error_code=e.response.status_code,
                    message=message,
                )
            return BackendResponse(
                response.json(), response.headers, response.status_code
            )

        url_params = self._get_url_params(**kwargs)
        for param in url_params:
            kwargs.pop(param)
        return _do_get(url, url_params, **kwargs)

    def _get_url(self, **kwargs) -> str:
        frames = getouterframes(currentframe())
        calling_function = frames[1].function
        raw_endpoint = self._endpoints.get(calling_function)

        if not raw_endpoint:
            raise UrlNotFoundError(calling_function)

        endpoint = raw_endpoint.format(**kwargs)
        url = parse.urljoin(self.base_url, endpoint)
        return url

    def _get_url_params(self, **kwargs) -> dict:
        frames = getouterframes(currentframe())
        calling_function = frames[2].function
        params = self._params.get(calling_function, []) + self._default_query_params

        return {param: value for param, value in kwargs.items() if param in params}

    def _get_raw_points(self, content: list) -> list:
        raw_points = [
            {
                self._field_map[attr]: value
                for attr, value in point.items()
                if attr in self._field_map
            }
            for point in content
        ]

        return raw_points
