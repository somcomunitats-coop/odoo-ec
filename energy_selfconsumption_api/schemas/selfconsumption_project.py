from pydantic import BaseModel


class SelfConsumptionProjectInfo(BaseModel):
    cau: str
    project_name: str
    ce_id: int
    ce_name: str
    # d'on surt aquests state????
    # state: int
    power: float


class SelfConsumptionProjectMember(BaseModel):
    cups: str
    cups_address: str
    cups_postalcode: str
    cups_town: str
    cups_state: str
    beta: float
    owner_name: str
    owner_surname1: str
    owner_surname2: str
    owner_vat: str
