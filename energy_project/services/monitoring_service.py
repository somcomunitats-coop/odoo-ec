from functools import lru_cache, reduce

from ..backends.base import Backend

# Functions to manage attributes access and operations
_get_energy_production = lambda point: float(point.get("energy_production", 0))
_get_energy_selfconsumption = lambda point: float(point.get("selfconsumption", 0))
_get_energy_exported = lambda point: float(point.get("energy_exported", 0))
_selfconsumption_ratio_pair = lambda accumulator, point: (
    accumulator[0] + _get_energy_selfconsumption(point),
    accumulator[1] + _get_energy_production(point),
)
_selfconsumption_surplus_ratio_pair = lambda accumulator, point: (
    accumulator[0] + _get_energy_exported(point),
    accumulator[1] + _get_energy_production(point),
)


class MonitoringService:
    def __init__(self, backend: Backend):
        self.backend = backend

    def generated_energy_by_member(self, system_id, member_id, date_from, date_to):
        daily_metrics = self._get_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        energy = sum(map(_get_energy_production, daily_metrics))
        return energy

    def energy_selfconsumed_ratio_by_member(
        self, system_id, member_id, date_from, date_to
    ):
        daily_metrics = self._get_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        selfconsumed_energy, generated_energy = reduce(
            _selfconsumption_ratio_pair, daily_metrics, (0, 0)
        )
        return round(selfconsumed_energy / generated_energy, 4)

    def energy_surplus_ratio_by_member(self, system_id, member_id, date_from, date_to):
        daily_metrics = self._get_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        selfconsumed_surplus_energy, generated_energy = reduce(
            _selfconsumption_surplus_ratio_pair, daily_metrics, (0, 0)
        )
        return round(selfconsumed_surplus_energy / generated_energy, 4)

    @lru_cache
    def _get_daily_metrics_by_member(self, system_id, member_id, from_date, to_date):
        return self.backend.project_daily_metrics_by_member(
            system_id, member_id, from_date, to_date
        )
