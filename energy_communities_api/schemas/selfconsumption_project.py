from pydantic import BaseModel


class SelfConsumptionProjectInfo(BaseModel):
    project_code: str
    project_name: str
    energy_community_id: int
    energy_community_name: str
    power: float


class SelfConsumptionProjectMember(BaseModel):
    supply_point_code: str
    supply_point_address: str
    supply_point_postalcode: str
    supply_point_town: str
    supply_point_state: str
    distribution_coefficient: float
    owner_name: str
    owner_surnames: str
    owner_vat: str
