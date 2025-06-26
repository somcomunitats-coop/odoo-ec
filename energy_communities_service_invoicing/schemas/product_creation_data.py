from typing import Optional

from pydantic import BaseModel, Field


class PackProductCreationData(BaseModel):
    categ_id: int
    name: str
    description_sale: str
    lst_price: float
    taxes_id: list
    recurring_rule_mode: str
    recurring_invoicing_type: str
    recurring_interval: Optional[int] = None
    recurring_rule_type: Optional[str] = None
    recurring_invoicing_fixed_type: Optional[str] = None
    fixed_invoicing_day: Optional[str] = None
    fixed_invoicing_month: Optional[str] = None


class ServiceProductCreationData(BaseModel):
    categ_id: int
    name: str
    description_sale: str
    lst_price: float
    taxes_id: list
    qty_type: Optional[str] = None
    quantity: Optional[float] = None
    qty_formula_ref: Optional[int] = None
