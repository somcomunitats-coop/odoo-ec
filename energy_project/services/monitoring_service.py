from functools import lru_cache, reduce

from ..backends.base import Backend

# Functions for attribute access
_get_energy_production = lambda point: float(point.get("energy_production", 0))
_get_energy_selfconsumption = lambda point: float(point.get("selfconsumption", 0))
_get_energy_exported = lambda point: float(point.get("energy_exported", 0))
_get_energy_consumption = lambda point: float(point.get("energy_consumption", 0))

# Functions for operations
_selfconsumption_ratio_pair = lambda accumulator, point: (
    accumulator[0] + _get_energy_selfconsumption(point),
    accumulator[1] + _get_energy_production(point),
)
_selfconsumption_surplus_ratio_pair = lambda accumulator, point: (
    accumulator[0] + _get_energy_exported(point),
    accumulator[1] + _get_energy_production(point),
)
_energy_usage_ratio_pair = lambda accumulator, point: (
    accumulator[0] + _get_energy_consumption(point),
    accumulator[1] + _get_energy_production(point),
)
_energy_usage_ratio_from_net_pair = lambda accumulator, point: (
    accumulator[0] + _get_energy_consumption(point),
    accumulator[1] + _get_energy_selfconsumption(point),
)
_energy_production_ratio_pair = lambda accumulator, point: (
    accumulator[0] + _get_energy_selfconsumption(point),
    accumulator[1] + _get_energy_consumption(point),
)


class MonitoringService:
    SPANISH_CO2_SAVE_RATIO = 162

    def __init__(self, backend: Backend):
        self.backend = backend

    def generated_energy_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        energy = sum(map(_get_energy_production, daily_metrics))
        return round(energy, 4)

    def consumed_energy_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        energy = sum(map(_get_energy_consumption, daily_metrics))
        return round(energy, 4)

    def exported_energy_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        energy = sum(map(_get_energy_exported, daily_metrics))
        return round(energy, 4)

    def selfconsumed_energy_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        energy = sum(map(_get_energy_selfconsumption, daily_metrics))
        return round(energy, 4)

    def selfconsumed_energy_ratio_by_member(
        self, system_id, member_id, date_from, date_to
    ):
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        selfconsumed_energy, generated_energy = reduce(
            _selfconsumption_ratio_pair, daily_metrics, (0, 0)
        )
        return round(selfconsumed_energy / generated_energy, 4)

    def energy_surplus_ratio_by_member(self, system_id, member_id, date_from, date_to):
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        selfconsumed_surplus_energy, generated_energy = reduce(
            _selfconsumption_surplus_ratio_pair, daily_metrics, (0, 0)
        )
        return round(selfconsumed_surplus_energy / generated_energy, 4)

    def co2save_by_member(self, system_id, member_id, date_from, date_to):
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        self_consumed_energy = sum(map(_get_energy_selfconsumption, daily_metrics))
        co2_saved = self_consumed_energy * self.SPANISH_CO2_SAVE_RATIO
        return co2_saved

    def generated_energy_by_project(self, system_id, date_from, date_to) -> float:
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        energy = sum(map(_get_energy_production, daily_metrics))
        return round(energy, 4)

    def selfconsumed_energy_by_project(self, system_id, date_from, date_to) -> float:
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        energy = sum(map(_get_energy_selfconsumption, daily_metrics))
        return round(energy, 4)

    def exported_energy_by_project(self, system_id, date_from, date_to) -> float:
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        energy = sum(map(_get_energy_exported, daily_metrics))
        return round(energy, 4)

    def energy_usage_ratio_by_member(self, system_id, member_id, date_from, date_to):
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        consumed_energy, generated_energy = reduce(
            _energy_usage_ratio_pair, daily_metrics, (0, 0)
        )
        return round(consumed_energy / generated_energy, 4)

    def energy_usage_ratio_from_net_by_member(
        self, system_id, member_id, date_from, date_to
    ):
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        consumed_energy, self_consumed_energy = reduce(
            _energy_usage_ratio_from_net_pair, daily_metrics, (0, 0)
        )
        return round((consumed_energy - self_consumed_energy) / consumed_energy, 4)

    def energy_production_ratio_by_member(
        self, system_id, member_id, date_from, date_to
    ):
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        self_consumed_energy, consumed_energy = reduce(
            _energy_production_ratio_pair, daily_metrics, (0, 0)
        )
        return round(self_consumed_energy / consumed_energy, 4)

    @lru_cache
    def _get_project_daily_metrics_by_member(
        self, system_id, member_id, from_date, to_date
    ):
        return self.backend.project_daily_metrics_by_member(
            system_id, member_id, from_date, to_date
        )

    @lru_cache
    def _get_project_daily_metrics(self, system_id, from_date, to_date):
        return self.backend.project_daily_metrics(system_id, from_date, to_date)
