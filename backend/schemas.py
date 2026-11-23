from datetime import date
from decimal import Decimal

from pydantic import computed_field
from sqlmodel import SQLModel

from models import Role


class StatusOut(SQLModel):
    id: int
    name: str
    position: int
    responsible_role: Role | None
    is_final: bool

    @computed_field
    @property
    def responsible_role_name(self) -> str | None:
        """The role's name for the board, e.g. "Bakery Manager" (empty for final columns)."""
        return self.responsible_role.display_name if self.responsible_role else None


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
    delay_reason: str | None
    delay_next_action: str | None
    is_overdue: bool
    awaiting_payment: bool


class ColumnOut(StatusOut):
    cards: list[CardOut]
