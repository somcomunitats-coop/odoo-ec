import logging
import requests
import json

from . import exceptions


logger = logging.getLogger(__name__)


class Client(object):
    """Client class
    This class manages the HTTP requests and this class only can send a request.
    """

    def __init__(self):
        self.baseurl = "https://web-testing.somcomunitats.coop/wp-json"

    def post(self, route, token=None, body=None):
        """Send a POST HTTP requests

        Args:
            route (str): String with the route to the endpoint
            body (dict): Dict with the body of the request to send

        Return:
            **response**: Return the response object
        """
        headers = {
            'Authorization': token,
        }
        return self._send_request(
            verb="POST", url=self._format_url(route), payload=body, extra_headers=headers
        )

    def put(self, route, token=None, body=None):
        """Send a PUT HTTP requests

        Args:
            route (str): String with the route to the endpoint
            body (dict): Dict with the body of the request to send

        Return:
            **response**: Return the response object
        """
        headers = {
            'Authorization': token,
        }
        return self._send_request(
            verb="PUT", url=self._format_url(route), payload=body, extra_headers=headers
        )

    def _format_url(self, path):
        return "{url}{path}".format(url=self.baseurl, path=path)

    def _send_request(self, verb, url, payload, extra_headers={}):
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

        logger.info("{verb} {url} \n {body}".format(verb=verb, url=url, body=payload))

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
