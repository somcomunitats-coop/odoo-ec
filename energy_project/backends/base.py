from collections import namedtuple
from inspect import currentframe, getouterframes
from urllib import parse

import requests

from .exceptions import RequestError, UrlNotFoundError

BackendResponse = namedtuple("BackendResponse", "content, headers, status")


class Backend:
    # Name of the authorization header
    AUTH_HEADER = "Authorization"

    # Default query params for all calls
    _default_query_params = []

    def _request(self, url, **kwargs) -> BackendResponse:
        """
        Closure to manage requests to external provider apis
        """

        def _do_get(url, url_params, **kwargs) -> BackendResponse:
            response = requests.get(url, params=url_params, **kwargs)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise RequestError(
                    error_code=e.response.status_code,
                    message=e.response.json().get("error", str(e)),
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
