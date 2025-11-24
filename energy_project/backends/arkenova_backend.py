from .base import Backend
from .domain import (
    EnergyCurve,
    EnergyPoint,
    EnergyPointAttributes,
    MeasurePoint,
)


class ArkenovaEnergyPoint(EnergyPoint):
    @property
    def gridconsumption(self):
        return self.consumption - self.selfconsumption

    @property
    def gridconsumption_measure(self) -> MeasurePoint:
        return MeasurePoint(date=self.date, value=self.gridconsumption)


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

    _field_map = {
        "energy_consumption": EnergyPointAttributes.CONSUMPTION.value,
        "energy_imported": EnergyPointAttributes.CONSUMPTION.value,
        "energy_exported": EnergyPointAttributes.GRIDINJECTION.value,
        "energy_production": EnergyPointAttributes.PRODUCTION.value,
        "selfconsumption": EnergyPointAttributes.SELFCONSUMPTION.value,
        "timestamp": EnergyPointAttributes.TIMESTAMP.value,
    }

    def __init__(self, url, token):
        self.base_url = url
        self._headers = {self.AUTH_HEADER: token}

    def project_daily_metrics(self, system_id, from_date, to_date) -> EnergyCurve:
        url = self._get_url(api_version=self._api_version, system_id=system_id)
        response = self._request(
            url, headers=self._headers, from_date=from_date, to_date=to_date
        )
        raw_points = self._get_raw_points(response.content)
        return [ArkenovaEnergyPoint(**point) for point in raw_points]

    def project_daily_metrics_by_member(
        self, system_id, member_id, from_date, to_date
    ) -> EnergyCurve:
        url = self._get_url(
            api_version=self._api_version, system_id=system_id, member_id=member_id
        )
        response = self._request(
            url, headers=self._headers, from_date=from_date, to_date=to_date
        )
        raw_points = self._get_raw_points(response.content)
        return [ArkenovaEnergyPoint(**point) for point in raw_points]
