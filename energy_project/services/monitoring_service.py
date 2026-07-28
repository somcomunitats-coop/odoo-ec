from functools import lru_cache, reduce
from typing import NamedTuple

from sentry_sdk import capture_exception

from ..backends.base import Backend
from ..backends.domain import EnergyCurve, MeasureCurve


class MetricPoint(NamedTuple):
    value: float
    consolidated: bool


NULL_POINT = MetricPoint(value=None, consolidated=None)


class MonitoringService:
    SPANISH_CO2_SAVE_RATIO = 162

    def __init__(self, backend: Backend):
        self.backend = backend

    def daily_gridconsumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MeasureCurve:
        """
        Daily energy consumption from the grid of a member in a shared selfconsumption project
        between two dates
        """
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        return MeasureCurve([point.gridconsumption_measure for point in daily_metrics])

    def energy_gridconsumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MetricPoint:
        """
        Total energy consumption from the grid of a member in a shared selfconsumption project
        between two dates
        """
        accumulate_gridconsumption = (
            lambda accumulator, point: accumulator + point.gridconsumption
        )
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        if daily_metrics:
            energy = reduce(
                accumulate_gridconsumption, daily_metrics.consolidated_points, 0.0
            )
            return MetricPoint(
                value=round(energy, 4), consolidated=daily_metrics.consolidated
            )
        return NULL_POINT

    def daily_gridinjection_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MeasureCurve:
        """
        Daily energy injection to the grid of a member in a shared selfconsumption project
        """
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        return MeasureCurve([point.gridinjection_measure for point in daily_metrics])

    def energy_gridinjection_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MetricPoint:
        """
        Total energy injected to the grid of a member in a shared selfconsumption project
        between two dates
        """
        accumulate_gridinjection = (
            lambda accumulator, point: accumulator + point.gridinjection
        )
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        if daily_metrics:
            energy = reduce(
                accumulate_gridinjection, daily_metrics.consolidated_points, 0.0
            )
            return MetricPoint(
                value=round(energy, 4), consolidated=daily_metrics.consolidated
            )
        return NULL_POINT

    def daily_selfconsumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MeasureCurve:
        """
        Daily selfconsumption of a member of a shared selfconsumption project
        """
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        return MeasureCurve([point.selfconsumption_measure for point in daily_metrics])

    def energy_selfconsumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MetricPoint:
        """
        Total energy selfconsumed of a member in a shared selfconsumption project
        between two dates
        """
        accumulate_selfconsumption = (
            lambda accumulator, point: accumulator + point.selfconsumption
        )
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        if daily_metrics:
            energy = reduce(
                accumulate_selfconsumption, daily_metrics.consolidated_points, 0.0
            )
            return MetricPoint(
                value=round(energy, 4), consolidated=daily_metrics.consolidated
            )
        return NULL_POINT

    def daily_consumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MeasureCurve:
        """
        Daily energy consumption from the grid of a member of a shared selfconsumption project
        """
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        return MeasureCurve([point.consumption_measure for point in daily_metrics])

    def energy_consumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MetricPoint:
        """
        Total energy consumed of a member in a shared selfconsumption project
        between two dates
        """
        accumulate_consumption = (
            lambda accumulator, point: accumulator + point.consumption
        )
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        if daily_metrics:
            energy = reduce(
                accumulate_consumption, daily_metrics.consolidated_points, 0.0
            )
            return MetricPoint(
                value=round(energy, 4), consolidated=daily_metrics.consolidated
            )
        return NULL_POINT

    def daily_production_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MeasureCurve:
        """
        Daily production of a shared selfconsumption project
        """
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        return MeasureCurve([point.production_measure for point in daily_metrics])

    def energy_production_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MetricPoint:
        """
        Total energy produced of a member in a shared selfconsumption project
        between two dates
        """
        accumulate_production = (
            lambda accumulator, point: accumulator + point.production
        )
        daily_metrics = self._get_project_daily_metrics_by_member(
            system_id, member_id, date_from, date_to
        )
        if daily_metrics:
            energy = reduce(
                accumulate_production, daily_metrics.consolidated_points, 0.0
            )
            return MetricPoint(
                value=round(energy, 4), consolidated=daily_metrics.consolidated
            )
        return NULL_POINT

    # TODO: Review this *_ratio_by_member methods. Should be production the total production
    # of the selfconsumption project instead of by member???
    def energy_selfconsumption_ratio_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MetricPoint:
        """
        Ratio between selfconsumed energy and produced energy of a member in a
        shared selfconsumption project between two dates
        """
        try:
            selfconsumption_ratio_accu = lambda accumulator, point: (
                accumulator[0] + point.selfconsumption,
                accumulator[1] + point.production,
            )
            daily_metrics = self._get_project_daily_metrics_by_member(
                system_id, member_id, date_from, date_to
            )
            selfconsumed_energy, produced_energy = reduce(
                selfconsumption_ratio_accu, daily_metrics.consolidated_points, (0, 0)
            )
            return MetricPoint(
                value=round(selfconsumed_energy / produced_energy, 4),
                consolidated=daily_metrics.consolidated,
            )
        except Exception as e:
            capture_exception(e)
            return NULL_POINT

    def energy_gridinjection_ratio_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MetricPoint:
        """
        Ratio between grid-injection energy and produced energy of a member in a
        shared selfconsumption project between two dates
        """
        try:
            surplus_ratio_accu = lambda accumulator, point: (
                accumulator[0] + point.gridinjection,
                accumulator[1] + point.production,
            )
            daily_metrics = self._get_project_daily_metrics_by_member(
                system_id, member_id, date_from, date_to
            )
            energy_gridinjection, energy_production = reduce(
                surplus_ratio_accu, daily_metrics.consolidated_points, (0, 0)
            )
            return MetricPoint(
                value=round(energy_gridinjection / energy_production, 4),
                consolidated=daily_metrics.consolidated,
            )
        except Exception as e:
            capture_exception(e)
            return NULL_POINT

    def energy_usage_ratio_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MetricPoint:
        """
        Ratio between energy produced and energy consumed of a member in a
        shared selfconsumption project between two dates
        """
        try:
            energy_usage_accu = lambda accumulator, point: (
                accumulator[0] + point.production,
                accumulator[1] + point.consumption,
            )
            daily_metrics = self._get_project_daily_metrics_by_member(
                system_id, member_id, date_from, date_to
            )
            energy_production, energy_consumption = reduce(
                energy_usage_accu, daily_metrics.consolidated_points, (0, 0)
            )
            return MetricPoint(
                value=round(energy_production / energy_consumption, 4),
                consolidated=daily_metrics.consolidated,
            )
        except Exception as e:
            capture_exception(e)
            return NULL_POINT

    def energy_usage_ratio_from_grid_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MetricPoint:
        """
        Ratio between energy consumed from the grid and energy consumed of a member in a
        shared selfconsumption project between two dates
        """
        try:
            energy_usage_ratio_from_grid_accu = lambda accumulator, point: (
                accumulator[0] + point.gridconsumption,
                accumulator[1] + point.consumption,
            )
            daily_metrics = self._get_project_daily_metrics_by_member(
                system_id, member_id, date_from, date_to
            )
            energy_gridconsumption, energy_consumption = reduce(
                energy_usage_ratio_from_grid_accu,
                daily_metrics.consolidated_points,
                (0, 0),
            )
            return MetricPoint(
                value=round(energy_gridconsumption / energy_consumption, 4),
                consolidated=daily_metrics.consolidated,
            )
        except Exception as e:
            capture_exception(e)
            return NULL_POINT

    def energy_usage_ratio_from_selfconsumption_by_member(
        self, system_id, member_id, date_from, date_to
    ) -> MetricPoint:
        """
        Ratio between energy selfconsumed and energy consumed of a member in a
        shared selfconsumption project between two dates
        """
        try:
            energy_production_ratio_accu = lambda accumulator, point: (
                accumulator[0] + point.selfconsumption,
                accumulator[1] + point.consumption,
            )
            daily_metrics = self._get_project_daily_metrics_by_member(
                system_id, member_id, date_from, date_to
            )
            energy_selfconsumption, energy_consumption = reduce(
                energy_production_ratio_accu, daily_metrics.consolidated_points, (0, 0)
            )
            return MetricPoint(
                value=round(energy_selfconsumption / energy_consumption, 4),
                consolidated=daily_metrics.consolidated,
            )
        except Exception as e:
            capture_exception(e)
            return NULL_POINT

    def co2save_by_member(self, system_id, member_id, date_from, date_to) -> float:
        """
        CO2 environmental saves of a member in a shared selfconsumption project between two dates
        """
        energy_production = self.energy_production_by_member(
            system_id, member_id, date_from, date_to
        )
        co2_saved = (
            energy_production
            and energy_production.value * self.SPANISH_CO2_SAVE_RATIO
            or 0.0
        )
        return co2_saved

    ## -- Project methods -- ##

    def daily_gridconsumption_by_project(
        self, system_id, date_from, date_to
    ) -> MeasureCurve:
        """
        Daily energy consumption from the grid of a shared selfconsumption project between two dates
        """
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        return MeasureCurve([point.gridconsumption_measure for point in daily_metrics])

    def energy_gridconsumption_by_project(
        self, system_id, date_from, date_to
    ) -> MetricPoint:
        """
        Total energy consumption from the grid of a shared selfconsumption project between two dates
        """
        accumulate_gridinjection = (
            lambda accumulator, point: accumulator + point.gridconsumption
        )
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        if daily_metrics:
            energy = reduce(
                accumulate_gridinjection, daily_metrics.consolidated_points, 0.0
            )
            return MetricPoint(
                value=round(energy, 4), consolidated=daily_metrics.consolidated
            )
        return NULL_POINT

    def daily_gridinjection_by_project(
        self, system_id, date_from, date_to
    ) -> MeasureCurve:
        """
        Daily energy injection to the grid of a shared selfconsumption project between two dates
        """
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        return MeasureCurve([point.gridinjection_measure for point in daily_metrics])

    def energy_gridinjection_by_project(
        self, system_id, date_from, date_to
    ) -> MetricPoint:
        """
        Total energy injection to the grid of a shared selfconsumption project between two dates
        """
        accumulate_gridinjection = (
            lambda accumulator, point: accumulator + point.gridinjection
        )
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        if daily_metrics:
            energy = reduce(
                accumulate_gridinjection, daily_metrics.consolidated_points, 0.0
            )
            return MetricPoint(
                value=round(energy, 4), consolidated=daily_metrics.consolidated
            )
        return NULL_POINT

    def daily_selfconsumption_by_project(
        self, system_id, date_from, date_to
    ) -> MeasureCurve:
        """
        Daily selfconsumption a shared selfconsumption project between two dates
        """
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        return MeasureCurve([point.selfconsumption_measure for point in daily_metrics])

    def energy_selfconsumption_by_project(
        self, system_id, date_from, date_to
    ) -> MetricPoint:
        """
        Total energy selfconsumed of a shared selfconsumption project between two dates
        """
        accumulate_selfconsumption = (
            lambda accumulator, point: accumulator + point.selfconsumption
        )
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        if daily_metrics:
            energy = reduce(
                accumulate_selfconsumption, daily_metrics.consolidated_points, 0.0
            )
            return MetricPoint(
                value=round(energy, 4), consolidated=daily_metrics.consolidated
            )
        return NULL_POINT

    def daily_consumption_by_project(
        self, system_id, date_from, date_to
    ) -> MeasureCurve:
        """
        Daily consumption of a shared selfconsumption project between two dates
        """
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        return MeasureCurve([point.consumption_measure for point in daily_metrics])

    def energy_consumption_by_project(
        self, system_id, date_from, date_to
    ) -> MetricPoint:
        """
        Total energy consumed of a shared selfconsumption project between two dates
        """
        accumulate_consumption = (
            lambda accumulator, point: accumulator + point.consumption
        )
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        if daily_metrics:
            energy = reduce(
                accumulate_consumption, daily_metrics.consolidated_points, 0.0
            )
            return MetricPoint(
                value=round(energy, 4), consolidated=daily_metrics.consolidated
            )
        return NULL_POINT

    def daily_production_by_project(
        self, system_id, date_from, date_to
    ) -> MeasureCurve:
        """
        Daily production of a shared selfconsumption project between two dates
        """
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        return MeasureCurve([point.production_measure for point in daily_metrics])

    def energy_production_by_project(
        self, system_id, date_from, date_to
    ) -> MetricPoint:
        """
        Total energy produced of a shared selfconsumption project between two dates
        """
        accumulate_production = (
            lambda accumulator, point: accumulator + point.production
        )
        daily_metrics = self._get_project_daily_metrics(system_id, date_from, date_to)
        if daily_metrics:
            energy = reduce(
                accumulate_production, daily_metrics.consolidated_points, 0.0
            )
            return MetricPoint(
                value=round(energy, 4), consolidated=daily_metrics.consolidated
            )
        return NULL_POINT

    def energy_selfconsumption_ratio(
        self, system_id, date_from, date_to
    ) -> MetricPoint:
        """
        Ratio between selfconsumed energy and produced energy of a shared
        selfconsumption project between two dates
        """
        try:
            selfconsumption_ratio_accu = lambda accumulator, point: (
                accumulator[0] + point.selfconsumption,
                accumulator[1] + point.production,
            )
            daily_metrics = self._get_project_daily_metrics(
                system_id, date_from, date_to
            )
            selfconsumed_energy, generated_energy = reduce(
                selfconsumption_ratio_accu, daily_metrics.consolidated_points, (0, 0)
            )
            return MetricPoint(
                value=round(selfconsumed_energy / generated_energy, 4),
                consolidated=daily_metrics.consolidated,
            )
        except Exception as e:
            capture_exception(e)
            return NULL_POINT

    def energy_gridinjection_ratio(self, system_id, date_from, date_to) -> MetricPoint:
        """
        Ratio between energy injected to the grid and produced energy of a shared
        selfconsumption project between two dates
        """
        try:
            surplus_ratio_accu = lambda accumulator, point: (
                accumulator[0] + point.gridinjection,
                accumulator[1] + point.production,
            )
            daily_metrics = self._get_project_daily_metrics(
                system_id, date_from, date_to
            )
            energy_gridinjection, energy_production = reduce(
                surplus_ratio_accu, daily_metrics.consolidated_points, (0, 0)
            )
            return MetricPoint(
                value=round(energy_gridinjection / energy_production, 4),
                consolidated=daily_metrics.consolidated,
            )
        except Exception as e:
            capture_exception(e)
            return NULL_POINT

    def energy_usage_ratio_from_grid(
        self, system_id, date_from, date_to
    ) -> MetricPoint:
        """
        Ratio between energy consumed from the grid and total energy consumed of a shared
        selfconsumption project between two dates
        """
        try:
            energy_usage_ratio_from_grid_accu = lambda accumulator, point: (
                accumulator[0] + point.gridconsumption,
                accumulator[1] + point.consumption,
            )
            daily_metrics = self._get_project_daily_metrics(
                system_id, date_from, date_to
            )
            energy_gridconsumption, energy_consumption = reduce(
                energy_usage_ratio_from_grid_accu,
                daily_metrics.consolidated_points,
                (0, 0),
            )
            return MetricPoint(
                value=round(energy_gridconsumption / energy_consumption, 4),
                consolidated=daily_metrics.consolidated,
            )
        except Exception as e:
            capture_exception(e)
            return NULL_POINT

    def energy_usage_ratio_from_selfconsumption(
        self, system_id, date_from, date_to
    ) -> MetricPoint:
        """
        Ratio between energy selfconsumed from the grid and total energy consumed of a shared
        selfconsumption project between two dates
        """
        try:
            energy_production_ratio_accu = lambda accumulator, point: (
                accumulator[0] + point.selfconsumption,
                accumulator[1] + point.consumption,
            )
            daily_metrics = self._get_project_daily_metrics(
                system_id, date_from, date_to
            )
            energy_selfconsumption, energy_consumption = reduce(
                energy_production_ratio_accu, daily_metrics.consolidated_points, (0, 0)
            )
            return MetricPoint(
                value=round(energy_selfconsumption / energy_consumption, 4),
                consolidated=daily_metrics.consolidated,
            )
        except Exception as e:
            capture_exception(e)
            return NULL_POINT

    def co2save_by_project(self, system_id, date_from, date_to) -> float:
        """
        CO2 environmental saves of a shared selfconsumption project between two dates
        """
        energy_production = self.energy_production_by_project(
            system_id, date_from, date_to
        )
        co2_saved = (
            energy_production
            and energy_production.value * self.SPANISH_CO2_SAVE_RATIO
            or 0.0
        )
        return co2_saved

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
