import requests

from .base import Backend
from .exceptions import RequestError


class ArkenovaBackend(Backend):
    """
    Backend implementation for arkenova api/rest communication
    """

    AUTH_HEADER = "apikey"

    _api_version = "v1"

    _endpoints = {
        "project_daily_metrics": "{api_version}/project/{system_id}",
        "project_daily_metrics_by_member": "{api_version}/project/{system_id}/members/{member_id}",
    }

    _default_query_params = [
        "from_date",
        "to_date",
    ]

    # query params for specific calls
    _params = {}

    def __init__(self, url, token):
        self.base_url = url

        self._headers = {self.AUTH_HEADER: token}

    def project_daily_metrics(self, system_id, from_date, to_date) -> list:
        url = self._get_url(api_version=self._api_version, system_id=system_id)
        response = self._request(
            url, headers=self._headers, from_date=from_date, to_date=to_date
        )

        return response.content

    def project_daily_metrics_by_member(
        self, system_id, member_id, from_date, to_date
    ) -> list:
        url = self._get_url(
            api_version=self._api_version, system_id=system_id, member_id=member_id
        )
        response = self._request(
            url, headers=self._headers, from_date=from_date, to_date=to_date
        )
        return response.content
