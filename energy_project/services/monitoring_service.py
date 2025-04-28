from functools import lru_cache, reduce

from sentry_sdk import capture_exception

from ..backends.base import Backend
from ..backends.domain import EnergyCurve, MeasureCurve

# Functions for operations


class MonitoringService:
    SPANISH_CO2_SAVE_RATIO = 162

    def __init__(self, backend: Backend):
        self.backend = backend

    def daily_consumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> EnergyCurve:
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        return [point.consumption_measure for point in daily_metrics]

    def daily_selfconsumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> EnergyCurve:
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        return [point.selfconsumption_measure for point in daily_metrics]

    def daily_gridconsumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> EnergyCurve:
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        return [point.gridconsumption_measure for point in daily_metrics]

    def daily_gridinjection_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> EnergyCurve:
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        return [point.gridinjection_measure for point in daily_metrics]

    def daily_production_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MeasureCurve:
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        return [point.production_measure for point in daily_metrics]

    def energy_consumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        accumulate_consumption = (
            lambda accumulator, point: accumulator + point.consumption
        )
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        if daily_metrics:
            energy = reduce(accumulate_consumption, daily_metrics, 0.0)
            return round(energy, 4)
        return 0.0

    def energy_selfconsumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        accumulate_selfconsumption = (
            lambda accumulator, point: accumulator + point.selfconsumption
        )
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        if daily_metrics:
            energy = reduce(accumulate_selfconsumption, daily_metrics, 0.0)
            return round(energy, 4)
        return 0.0

    def energy_gridconsumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        accumulate_gridconsumption = (
            lambda accumulator, point: accumulator + point.gridconsumption
        )
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        if daily_metrics:
            energy = reduce(accumulate_gridconsumption, daily_metrics, 0.0)
            return round(energy, 4)
        return 0.0

    def energy_gridinjection_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        accumulate_gridinjection = (
            lambda accumulator, point: accumulator + point.gridinjection
        )
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        if daily_metrics:
            energy = reduce(accumulate_gridinjection, daily_metrics, 0.0)
            return round(energy, 4)
        return 0.0

    def energy_production_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        accumulate_production = (
            lambda accumulator, point: accumulator + point.production
        )
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        if daily_metrics:
            energy = reduce(accumulate_production, daily_metrics, 0.0)
            return round(energy, 4)
        return 0.0

    def energy_selfconsumption_ratio_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        try:
            selfconsumption_ratio_accu = lambda accumulator, point: (
                accumulator[0] + point.selfconsumption,
                accumulator[1] + point.production,
            )
            daily_metrics = self._get_project_daily_metrics_by_member(
                system_id, member_id, date_from, date_to
            )
            selfconsumed_energy, generated_energy = reduce(
                selfconsumption_ratio_accu, daily_metrics, (0, 0)
            )
            return round(selfconsumed_energy / generated_energy, 4)
        except Exception as e:
            capture_exception(e)
            return 0.0

    def energy_surplus_ratio_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        try:
            surplus_ratio_accu = lambda accumulator, point: (
                accumulator[0] + point.gridinjection,
                accumulator[1] + point.production,
            )
            daily_metrics = self._get_project_daily_metrics_by_member(
                system_id, member_id, date_from, date_to
            )
            energy_gridinjection, energy_production = reduce(
                surplus_ratio_accu, daily_metrics, (0, 0)
            )
            return round(energy_gridinjection / energy_production, 4)
        except Exception as e:
            capture_exception(e)
            return 0.0

    def energy_usage_ratio_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        try:
            energy_usage_accu = lambda accumulator, point: (
                accumulator[0] + point.production,
                accumulator[1] + point.consumption,
            )
            daily_metrics = self._get_project_daily_metrics_by_member(
                system_id, member_id, date_from, date_to
            )
            energy_production, energy_consumption = reduce(
                energy_usage_accu, daily_metrics, (0, 0)
            )
            return round(energy_production / energy_consumption, 4)
        except Exception as e:
            capture_exception(e)
            return 0.0

    def energy_usage_ratio_from_grid_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        try:
            energy_usage_ratio_from_grid_accu = lambda accumulator, point: (
                accumulator[0] + point.gridconsumption,
                accumulator[1] + point.consumption,
            )
            daily_metrics = self._get_project_daily_metrics_by_member(
                system_id, member_id, date_from, date_to
            )
            energy_gridconsumption, energy_consumption = reduce(
                energy_usage_ratio_from_grid_accu, daily_metrics, (0, 0)
            )
            return round(energy_gridconsumption / energy_consumption, 4)
        except Exception as e:
            capture_exception(e)
            return 0.0

    def energy_usage_ratio_from_selfconsumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> float:
        try:
            energy_production_ratio_accu = lambda accumulator, point: (
                accumulator[0] + point.selfconsumption,
                accumulator[1] + point.consumption,
            )
            daily_metrics = self._get_project_daily_metrics_by_member(
                system_id, member_id, date_from, date_to
            )
            energy_selfconsumption, energy_consumption = reduce(
                energy_production_ratio_accu, daily_metrics, (0, 0)
            )
            return round(energy_selfconsumption / energy_consumption, 4)
        except Exception as e:
            capture_exception(e)
            return 0.0

    def co2save_by_member(self, system_id, member_id, date_from, date_to) -> float:
        energy_production = self.energy_production_by_member(
            system_id, member_id, date_from, date_to
        )
        co2_saved = energy_production * self.SPANISH_CO2_SAVE_RATIO
        return co2_saved

    ## -- Project methods -- ##
    def energy_production_by_project(self, system_id, date_from, date_to) -> float:
        accumulate_production = (
            lambda accumulator, point: accumulator + point.production
        )
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        if daily_metrics:
            energy = reduce(accumulate_production, daily_metrics, 0.0)
            return round(energy, 4)
        return 0.0

    def energy_consumption_by_project(self, system_id, date_from, date_to) -> float:
        accumulate_consumption = (
            lambda accumulator, point: accumulator + point.consumption
        )
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        if daily_metrics:
            energy = reduce(accumulate_consumption, daily_metrics, 0.0)
            return round(energy, 4)
        return 0.0

    def energy_gridinjection_by_project(self, system_id, date_from, date_to) -> float:
        accumulate_gridinjection = (
            lambda accumulator, point: accumulator + point.gridinjection
        )
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        if daily_metrics:
            energy = reduce(accumulate_gridinjection, daily_metrics, 0.0)
            return round(energy, 4)
        return 0.0

    def energy_selfconsumption_by_project(self, system_id, date_from, date_to) -> float:
        accumulate_selfconsumption = (
            lambda accumulator, point: accumulator + point.selfconsumption
        )
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        if daily_metrics:
            energy = reduce(accumulate_selfconsumption, daily_metrics, 0.0)
            return round(energy, 4)
        return 0.0

    def energy_selfconsumption_ratio(self, system_id, date_from, date_to) -> float:
        try:
            selfconsumption_ratio_accu = lambda accumulator, point: (
                accumulator[0] + point.selfconsumption,
                accumulator[1] + point.production,
            )
            daily_metrics = self._get_project_daily_metrics(
                system_id, date_from, date_to
            )
            selfconsumed_energy, generated_energy = reduce(
                selfconsumption_ratio_accu, daily_metrics, (0, 0)
            )
            return round(selfconsumed_energy / generated_energy, 4)
        except Exception as e:
            capture_exception(e)
            return 0.0

    def energy_surplus_ratio(self, system_id, date_from, date_to) -> float:
        try:
            surplus_ratio_accu = lambda accumulator, point: (
                accumulator[0] + point.gridinjection,
                accumulator[1] + point.production,
            )
            daily_metrics = self._get_project_daily_metrics(
                system_id, date_from, date_to
            )
            energy_gridinjection, energy_production = reduce(
                surplus_ratio_accu, daily_metrics, (0, 0)
            )
            return round(energy_gridinjection / energy_production, 4)
        except Exception as e:
            capture_exception(e)
            return 0.0

    def energy_usage_ratio_from_grid(self, system_id, date_from, date_to) -> float:
        try:
            energy_usage_ratio_from_grid_accu = lambda accumulator, point: (
                accumulator[0] + point.gridconsumption,
                accumulator[1] + point.consumption,
            )
            daily_metrics = self._get_project_daily_metrics(
                system_id, date_from, date_to
            )
            energy_gridconsumption, energy_consumption = reduce(
                energy_usage_ratio_from_grid_accu, daily_metrics, (0, 0)
            )
            return round(energy_gridconsumption / energy_consumption, 4)
        except Exception as e:
            capture_exception(e)
            return 0.0

    def energy_usage_ratio_from_selfconsumption(
        self, system_id, date_from, date_to
    ) -> float:
        try:
            energy_production_ratio_accu = lambda accumulator, point: (
                accumulator[0] + point.selfconsumption,
                accumulator[1] + point.consumption,
            )
            daily_metrics = self._get_project_daily_metrics(
                system_id, date_from, date_to
            )
            energy_selfconsumption, energy_consumption = reduce(
                energy_production_ratio_accu, daily_metrics, (0, 0)
            )
            return round(energy_selfconsumption / energy_consumption, 4)
        except Exception as e:
            capture_exception(e)
            return 0.0

    def co2save_by_project(self, system_id, date_from, date_to) -> float:
        energy_production = self.energy_production_by_project(
            system_id, date_from, date_to
        )
        co2_saved = energy_production * self.SPANISH_CO2_SAVE_RATIO
        return co2_saved

    def daily_consumption_by_project(
        self, system_id, date_from, date_to
    ) -> EnergyCurve:
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        return [point.consumption_measure for point in daily_metrics]

    def daily_selfconsumption_by_project(
        self, system_id, date_from, date_to
    ) -> EnergyCurve:
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        return [point.selfconsumption_measure for point in daily_metrics]

    def daily_gridinjection_by_project(
        self, system_id, date_from, date_to
    ) -> EnergyCurve:
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        return [point.gridinjection_measure for point in daily_metrics]

    def daily_production_by_project(
        self, system_id, date_from, date_to
    ) -> MeasureCurve:
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        return [point.production_measure for point in daily_metrics]

    @lru_cache
    def _get_project_daily_metrics_by_member(
        self, system_id, member_id, from_date, to_date
    ) -> EnergyCurve:
        return self.backend.project_daily_metrics_by_member(
            system_id, member_id, from_date, to_date
        )

    @lru_cache
    def _get_project_daily_metrics(self, system_id, from_date, to_date) -> EnergyCurve:
        return self.backend.project_daily_metrics(system_id, from_date, to_date)
