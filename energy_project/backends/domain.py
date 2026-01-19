from collections import namedtuple
from enum import Enum
from typing import Any, List

MeasurePoint = namedtuple("MeasurePoint", ["date", "value"])
MeasureCurve = List[MeasurePoint]


class EnergyPointAttributes(Enum):
    """ "
    Default name attributes. These are the names that we will use to map privider attributes
    to energy_community_api attributes
    """

    SELFCONSUMPTION: str = "selfconsumption"
    CONSUMPTION: str = "consumption"
    GRIDINJECTION: str = "gridinjection"
    PRODUCTION: str = "production"
    TIMESTAMP: str = "date"


class EnergyPoint(
    namedtuple("EnergyPoint", [attr.value for attr in EnergyPointAttributes])
):
    __slots__ = ()

    def __getattribute__(self, name: str) -> Any:
        __float_attrs = [
            EnergyPointAttributes.SELFCONSUMPTION.value,
            EnergyPointAttributes.CONSUMPTION.value,
            EnergyPointAttributes.GRIDINJECTION.value,
            EnergyPointAttributes.PRODUCTION.value,
        ]
        value = super().__getattribute__(name)
        if name in __float_attrs:
            return float(value) if value is not None else 0
        return value

    @property
    def gridinjection_measure(self) -> MeasurePoint:
        return MeasurePoint(date=self.date, value=self.gridinjection)

    @property
    def production_measure(self) -> MeasurePoint:
        return MeasurePoint(date=self.date, value=self.production)

    @property
    def selfconsumption_measure(self) -> MeasurePoint:
        return MeasurePoint(date=self.date, value=self.selfconsumption)

    @property
    def consumption_measure(self) -> MeasurePoint:
        return MeasurePoint(date=self.date, value=self.consumption)


EnergyCurve = List[EnergyPoint]
