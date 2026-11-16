from datetime import date, datetime, timezone
from decimal import Decimal
from sqlmodel import SQLModel, Field

class Supplier(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    phone: str
    address: str

class Ingredient(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    unit: str
    price_per_unit: Decimal = Field(max_digits=8, decimal_places=2)
    regular_restock_qty: Decimal = Field(max_digits=8, decimal_places=2)
    usual_delivery_days: int
    supplier_id: int = Field(foreign_key="supplier.id")

class RestockStatus(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    position: int

class RestockCard(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredient.id")
    status_id: int = Field(foreign_key="restockstatus.id")
    supplier_id: int = Field(foreign_key="supplier.id")
    quantity: Decimal = Field(max_digits=8, decimal_places=2)
    unit_price: Decimal = Field(max_digits=8, decimal_places=2)
    expected_delivery_date: date | None = None
    delay_reason: str | None = None
    delay_next_action: str | None = None
    position: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))