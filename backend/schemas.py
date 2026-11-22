from datetime import date
from decimal import Decimal

from sqlmodel import SQLModel


class CardOut(SQLModel):
    id: int
    ingredient: str
    unit: str
    quantity: Decimal
    unit_price: Decimal
    estimated_total: Decimal
    supplier: str
    expected_delivery_date: date | None
    is_paid: bool


class ColumnOut(SQLModel):
    id: int
    name: str
    position: int
    cards: list[CardOut]