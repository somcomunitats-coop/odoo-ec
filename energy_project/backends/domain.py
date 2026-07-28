from collections import UserList, namedtuple
from dataclasses import make_dataclass
from enum import Enum


class EnergyPointAttributes(Enum):
    """
    Default name attributes. These are the names that we will use to map privider
    attributes to energy_community_api attributes
    """

    GRIDCONSUMPTION: str = "_gridconsumption"
    GRIDINJECTION: str = "_gridinjection"
    SELFCONSUMPTION: str = "_selfconsumption"
    CONSUMPTION: str = "_consumption"
    PRODUCTION: str = "_production"
    TIMESTAMP: str = "date"


BaseEnergyPoint = make_dataclass(
    "BaseEnergyPoint", [attr.value for attr in EnergyPointAttributes]
)

MeasurePoint = namedtuple("MeasurePoint", ["date", "value", "consolidated"])


class EnergyPoint(BaseEnergyPoint):
    @property
    def gridconsumption(self):
        return self._gridconsumption

    @property
    def gridconsumption_measure(self) -> MeasurePoint:
        return MeasurePoint(
            date=self.date, value=self.gridconsumption, consolidated=self.consolidated
        )

    @property
    def gridinjection(self):
        return self._gridinjection

    @property
    def gridinjection_measure(self) -> MeasurePoint:
        return MeasurePoint(
            date=self.date, value=self.gridinjection, consolidated=self.consolidated
        )

    @property
    def selfconsumption(self):
        return self._selfconsumption

    @property
    def selfconsumption_measure(self) -> MeasurePoint:
        return MeasurePoint(
            date=self.date, value=self.selfconsumption, consolidated=self.consolidated
        )

    @property
    def consumption(self):
        return self._consumption

    @property
    def consumption_measure(self) -> MeasurePoint:
        return MeasurePoint(
            date=self.date, value=self.consumption, consolidated=self.consolidated
        )

    @property
    def production(self):
        return self._production

    @property
    def production_measure(self) -> MeasurePoint:
        return MeasurePoint(
            date=self.date, value=self.production, consolidated=self.consolidated
        )

    @property
    def consolidated(self) -> bool:
        return True


class Curve(UserList):
    """
    List of EnergyPoints
    """

    @property
    def consolidated_points(self):
        return [elem for elem in self.data if elem.consolidated]

    @property
    def consolidated(self):
        return all([elem.consolidated for elem in self.data])


EnergyCurve = Curve[EnergyPoint]
MeasureCurve = Curve[MeasurePoint]
