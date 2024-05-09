from urllib import parse

import requests

from .exceptions import RequestError


class ArkenovaBackend:
    ENDPOINTS = {
        "project_metrics": "v1/project/{system_id}",
    }

    HEADERS = {}

    def __init__(self, url, token):
        self.base_url = url
        self.token = token
        self.HEADERS["apikey"] = self.token

    def project_daily_metrics(self, system_id, from_date, to_date):
        url = parse.urljoin(
            self.base_url, self.ENDPOINTS["project_metrics"].format(system_id=system_id)
        )
        query_params = {"from_date": from_date, "to_date": to_date}

        response = requests.get(url, headers=self.HEADERS, params=query_params)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise RequestError(
                error_code=e.response.status_code,
                message=e.response.json().get("error", str(e)),
            )
        return response.json()
