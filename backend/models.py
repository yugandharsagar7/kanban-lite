from datetime import date, datetime, timezone
from decimal import Decimal
from sqlmodel import SQLModel, Field
from enum import Enum
from sqlalchemy import CheckConstraint, Column, Enum as SAEnum, UniqueConstraint


class Unit(str, Enum):
    kg = "kg"
    litres = "litres"
    dozen = "dozen"
    pieces = "pieces"


class ReviewSession(str, Enum):
    morning = "morning"
    afternoon = "afternoon"


class CardAction(str, Enum):
    created = "created"
    moved = "moved"
    edited = "edited"
    paid = "paid"
    deleted = "deleted"


class Role(str, Enum):
    # Stored as codes without spaces, so they can match Entra ID app role values.
    kitchen_assistant = "kitchen_assistant"
    head_chef = "head_chef"
    bakery_manager = "bakery_manager"
    owner = "owner"

    @property
    def display_name(self) -> str:
        """The name shown on the board, e.g. "Bakery Manager"."""
        return ROLE_DISPLAY_NAMES[self]


ROLE_DISPLAY_NAMES = {
    Role.kitchen_assistant: "Kitchen Assistant",
    Role.head_chef: "Head Chef",
    Role.bakery_manager: "Bakery Manager",
    Role.owner: "Owner",
}


def enum_column(enum_class, name, nullable=False):
    """A database column that only accepts this Enum's values."""
    return Column(
        SAEnum(
            enum_class,
            name=name,
            values_callable=lambda e: [member.value for member in e],
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=nullable,
    )


class Supplier(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    phone: str
    address: str

class Ingredient(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("price_per_unit >= 0", name="ck_ingredient_price"),
        CheckConstraint("regular_restock_qty > 0", name="ck_ingredient_restock_qty"),
        CheckConstraint("usual_delivery_days >= 0", name="ck_ingredient_delivery_days"),
    )
    id: int | None = Field(default=None, primary_key=True)
    name: str
    unit: Unit = Field(sa_column=enum_column(Unit, "unit"))
    price_per_unit: Decimal = Field(max_digits=10, decimal_places=4)
    regular_restock_qty: Decimal = Field(max_digits=10, decimal_places=3)
    usual_delivery_days: int
    supplier_id: int = Field(foreign_key="supplier.id")

class RestockStatus(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint(
            "(is_final = 1 AND responsible_role IS NULL)"
            " OR (is_final = 0 AND responsible_role IS NOT NULL)",
            name="ck_status_role_unless_final",
        ),
    )
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    position: int = Field(unique=True)
    responsible_role: Role | None = Field(
        default=None, sa_column=enum_column(Role, "role", nullable=True)
    )
    is_final: bool = False

class RestockCard(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_card_quantity"),
        CheckConstraint("unit_price >= 0", name="ck_card_unit_price"),
        CheckConstraint(
            "(deleted_at IS NULL AND deleted_by IS NULL AND deleted_reason IS NULL)"
            " OR (deleted_at IS NOT NULL AND deleted_by IS NOT NULL"
            " AND deleted_reason IS NOT NULL"
            " AND trim(deleted_by) <> '' AND trim(deleted_reason) <> '')",
            name="ck_card_delete_all_or_none",
        ),
        CheckConstraint(
            "(paid_at IS NULL AND paid_by IS NULL)"
            " OR (paid_at IS NOT NULL AND paid_by IS NOT NULL"
            " AND trim(paid_by) <> '')",
            name="ck_card_paid_all_or_none",
        ),
        CheckConstraint(
            "paid_at IS NULL OR deleted_at IS NULL",
            name="ck_card_paid_not_deleted",
        ),
    )
    id: int | None = Field(default=None, primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredient.id")
    status_id: int = Field(foreign_key="restockstatus.id")
    supplier_id: int = Field(foreign_key="supplier.id")
    quantity: Decimal = Field(max_digits=10, decimal_places=3)
    unit_price: Decimal = Field(max_digits=10, decimal_places=4)
    expected_delivery_date: date | None = None
    delay_reason: str | None = None
    delay_next_action: str | None = None
    position: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    paid_at: datetime | None = None
    paid_by: str | None = None
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    deleted_reason: str | None = None

class CardEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    card_id: int = Field(foreign_key="restockcard.id")
    action: CardAction = Field(sa_column=enum_column(CardAction, "card_action"))
    from_status_id: int | None = Field(default=None, foreign_key="restockstatus.id")
    to_status_id: int | None = Field(default=None, foreign_key="restockstatus.id")
    actor: str
    note: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReviewSignOff(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("business_date", "session", name="uq_signoff_date_session"),
        CheckConstraint("items_reviewed >= 0", name="ck_signoff_items_reviewed"),
    )
    id: int | None = Field(default=None, primary_key=True)
    business_date: date
    session: ReviewSession = Field(sa_column=enum_column(ReviewSession, "review_session"))
    signed_by: str
    items_reviewed: int
    signed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))