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