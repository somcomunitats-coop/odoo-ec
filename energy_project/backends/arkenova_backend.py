from .base import Backend
from .domain import Curve, EnergyCurve, EnergyPoint, EnergyPointAttributes


class ArkenovaEnergyPoint(EnergyPoint):
    @property
    def gridconsumption(self):
        if self.consolidated:
            return self._gridconsumption

    @property
    def consumption(self):
        if self.consolidated:
            return self._gridconsumption + self._selfconsumption
        return self._gridconsumption

    @property
    def consolidated(self) -> bool:
        return bool(self._selfconsumption)


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
        "energy_imported": EnergyPointAttributes.GRIDCONSUMPTION.value,
        "energy_consumption": EnergyPointAttributes.CONSUMPTION.value,
        "energy_exported": EnergyPointAttributes.GRIDINJECTION.value,
        "selfconsumption": EnergyPointAttributes.SELFCONSUMPTION.value,
        "energy_production": EnergyPointAttributes.PRODUCTION.value,
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
        return Curve([ArkenovaEnergyPoint(**point) for point in raw_points])

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
        return Curve([ArkenovaEnergyPoint(**point) for point in raw_points])
