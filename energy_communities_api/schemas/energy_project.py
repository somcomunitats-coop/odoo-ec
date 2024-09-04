from datetime import date

from pydantic import BaseModel, Field


class EnergyPoint(BaseModel):
    value: float = Field(..., title="Value", description="Value in kWh of the point")
    date_: date = Field(
        ...,
        alias="date",
        title="Date",
        description="Date (ex. 2024-06-01) of the value",
    )
