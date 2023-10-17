import json
import logging

import requests

from . import exceptions

logger = logging.getLogger(__name__)


class Client:
    """Client class
    This class manages the HTTP requests and this class only can send a request.
    """

    def __init__(self, baseurl):
        self.baseurl = baseurl

    def get(self, route, token=None):
        """Send a GET HTTP requests

        Args:
            route (str): String with the route to the endpoint

        Return:
            **response**: Return the response object
        """
        headers = {"Authorization": token, "Content-Type": "application/json"}
        return self._send_request(
            verb="GET",
            url=self._format_url(route),
            payload={},
            extra_headers=headers,
        )

    def post(self, route, token=None, body=None):
        """Send a POST HTTP requests

        Args:
            route (str): String with the route to the endpoint
            body (dict): Dict with the body of the request to send

        Return:
            **response**: Return the response object
        """
        headers = {"Authorization": token, "Content-Type": "application/json"}
        return self._send_request(
            verb="POST",
            url=self._format_url(route),
            payload=body,
            extra_headers=headers,
        )

    def put(self, route, token=None, body=None):
        """Send a PUT HTTP requests

        Args:
            route (str): String with the route to the endpoint
            body (dict): Dict with the body of the request to send

        Return:
            **response**: Return the response object
        """
        headers = {"Authorization": token, "Content-Type": "application/json"}
        return self._send_request(
            verb="PUT", url=self._format_url(route), payload=body, extra_headers=headers
        )

    def _format_url(self, path):
        return "{url}{path}".format(url=self.baseurl, path=path)

    # TODO extra_headers check if default value {} is needed
    def _send_request(self, verb, url, payload, extra_headers):
        """send the API request using the *requests.request* method

        Args:
            payload (dict)

        Raises:
            HTTPError:
            ArgumentMissingError

        Returns:
            **requests.Response**: Response received after sending the request.

        .. note::
            Supported HTTP Methods: DELETE, GET, HEAD, PATCH, POST, PUT
        """
        headers = {
            "Accept": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)

        if headers.get("Content-Type") == "application/json":
            payload = json.dumps(payload)

        logger.info("{verb} {url}".format(verb=verb, url=url))

        try:
            response = requests.request(
                verb.upper(), url, headers=headers, data=payload
            )

        except Exception as err:
            raise exceptions.HTTPError(err)
        if response.status_code == 500:
            raise exceptions.HTTPError(response.reason)
        if response.status_code not in [200, 201]:
            raise exceptions.NotSuccessfulRequest(response.status_code)
        return response.json()
