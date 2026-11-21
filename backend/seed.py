"""Fill the database with made-up demo data for Sunrise Bakery.

Run from the backend folder:  python seed.py

Every run deletes all tables, recreates them and inserts fresh demo data, so it
only runs against SQLite. All names, phone numbers, addresses and prices are
made up. Phone numbers use the 555-0100 to 555-0199 range reserved for fiction.
"""

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from sqlmodel import Session, SQLModel

from models import (
    CardAction,
    CardEvent,
    Ingredient,
    RestockCard,
    RestockStatus,
    ReviewSession,
    ReviewSignOff,
    Supplier,
    Unit,
)
from settings import BAKERY_TIMEZONE, bakery_today

# The six columns, in board order (from docs/requirements.md).
STATUS_NAMES = [
    "Running low",
    "Manager review",
    "Owner review",
    "Ordered",
    "Restocked",
    "Delayed",
]

# Made-up people.
KITCHEN = "Kitchen Jo"
CHEF = "Chef Sam"
MANAGER = "Manager Alex"
OWNER = "Owner Morgan"

# Whose turn it is in each column, so who moves a card out of it.
MOVED_BY = {
    "Running low": CHEF,
    "Manager review": MANAGER,
    "Owner review": OWNER,
    "Ordered": MANAGER,
    "Delayed": MANAGER,
}


class NotSQLiteError(Exception):
    """Raised when the seed is pointed at a database that isn't SQLite."""


def bakery_time(days_ago, hour, minute=0):
    """A clock time at the bakery, some days ago, converted to UTC for storage."""
    day = bakery_today() - timedelta(days=days_ago)
    local = datetime.combine(day, time(hour, minute), tzinfo=BAKERY_TIMEZONE)
    return local.astimezone(timezone.utc)


def seed(engine):
    """Delete all tables, recreate them and insert fresh demo data."""
    if engine.dialect.name != "sqlite":
        raise NotSQLiteError(
            "Refusing to seed: seed.py deletes every table, and DATABASE_URL does "
            "not point to a SQLite database. Unset DATABASE_URL to use the local "
            "kanban.db, or point it to another SQLite file."
        )

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        statuses = add_statuses(session)
        ingredients = add_suppliers_and_ingredients(session)
        add_cards(session, statuses, ingredients)
        add_signoffs(session)
        session.commit()


def add_statuses(session):
    """The six columns, in board order. Returns them by name."""
    statuses = {}
    for position, name in enumerate(STATUS_NAMES, start=1):
        statuses[name] = RestockStatus(name=name, position=position)
        session.add(statuses[name])
    session.flush()  # send to the database now, so each row gets its id
    return statuses


def add_suppliers_and_ingredients(session):
    """3 suppliers and 8 ingredients, using every unit. Returns ingredients by name."""
    mill = Supplier(
        name="Golden Mill Supplies",
        phone="(212) 555-0101",
        address="100 Millstone Way, Hollow Creek",
    )
    dairy = Supplier(
        name="Meadow Lane Dairy",
        phone="(212) 555-0102",
        address="42 Pasture Road, Hollow Creek",
    )
    spice = Supplier(
        name="Orchard Spice Traders",
        phone="(212) 555-0103",
        address="7 Cardamom Court, Hollow Creek",
    )
    session.add_all([mill, dairy, spice])
    session.flush()

    # name, unit, price per unit, regular restock quantity, usual delivery days, supplier
    rows = [
        ("Bread flour", Unit.kg, "0.8800", "25", 3, mill),
        ("Granulated sugar", Unit.kg, "1.1500", "10", 3, mill),
        ("Saffron", Unit.kg, "4250.0000", "0.125", 7, spice),
        ("Unsalted butter", Unit.kg, "9.2500", "5", 2, dairy),
        ("Whole milk", Unit.litres, "1.0500", "12", 1, dairy),
        ("Heavy cream", Unit.litres, "4.3750", "4", 2, dairy),
        ("Free-range eggs", Unit.dozen, "3.6000", "15", 3, mill),
        ("Vanilla pods", Unit.pieces, "2.4500", "20", 5, spice),
    ]
    ingredients = {}
    for name, unit, price, quantity, days, supplier in rows:
        ingredients[name] = Ingredient(
            name=name,
            unit=unit,
            price_per_unit=Decimal(price),
            regular_restock_qty=Decimal(quantity),
            usual_delivery_days=days,
            supplier_id=supplier.id,
        )
    session.add_all(ingredients.values())
    session.flush()
    return ingredients


def add_card(
    session,
    statuses,
    ingredient,
    created_at,
    moves=(),
    hours_between=6,
    notes=None,
    quantity=None,
    position=0,
    **extra,
):
    """Create one card and its matching history.

    moves lists the columns the card moved to, in order, after starting in
    Running low. The card is placed in the last one, and each move becomes a
    "moved" event, so the card and its history can't disagree.
    notes maps a move's number (1 = first move) to the note for that move.
    Returns the card and the time of its last move.
    """
    notes = notes or {}
    final_column = moves[-1] if moves else "Running low"

    card = RestockCard(
        ingredient_id=ingredient.id,
        status_id=statuses[final_column].id,
        # Snapshot: the card keeps the supplier and price at the time of the order.
        supplier_id=ingredient.supplier_id,
        unit_price=ingredient.price_per_unit,
        quantity=quantity if quantity is not None else ingredient.regular_restock_qty,
        position=position,
        created_at=created_at,
        **extra,
    )
    session.add(card)
    session.flush()

    session.add(
        CardEvent(
            card_id=card.id,
            action=CardAction.created,
            to_status_id=statuses["Running low"].id,
            actor=KITCHEN,
            timestamp=created_at,
        )
    )
    current = "Running low"
    when = created_at
    for number, destination in enumerate(moves, start=1):
        when += timedelta(hours=hours_between)
        session.add(
            CardEvent(
                card_id=card.id,
                action=CardAction.moved,
                from_status_id=statuses[current].id,
                to_status_id=statuses[destination].id,
                actor=MOVED_BY[current],
                note=notes.get(number),
                timestamp=when,
            )
        )
        current = destination
    return card, when


def add_cards(session, statuses, ingredients):
    """10 cards across all six columns."""
    today = bakery_today()
    to_ordered = ["Manager review", "Owner review", "Ordered"]

    # 1. Running low: flagged in the last hour, regular quantity.
    add_card(
        session, statuses, ingredients["Bread flour"],
        created_at=datetime.now(timezone.utc) - timedelta(minutes=45),
    )

    # 2. Running low: more milk than usual for a busy weekend.
    add_card(
        session, statuses, ingredients["Whole milk"],
        created_at=bakery_time(days_ago=1, hour=16),
        quantity=Decimal("18"), position=1,
    )

    # 3. Manager review.
    add_card(
        session, statuses, ingredients["Granulated sugar"],
        created_at=bakery_time(days_ago=1, hour=8),
        moves=["Manager review"], hours_between=3,
    )

    # 4. Manager review, after the owner moved it back with a note.
    add_card(
        session, statuses, ingredients["Saffron"],
        created_at=bakery_time(days_ago=3, hour=8),
        moves=["Manager review", "Owner review", "Manager review"], hours_between=4,
        notes={3: "Price looks high, please check another supplier."},
        position=1,
    )

    # 5. Owner review.
    add_card(
        session, statuses, ingredients["Unsalted butter"],
        created_at=bakery_time(days_ago=2, hour=8),
        moves=["Manager review", "Owner review"], hours_between=5,
    )

    # 6. Ordered, delivery expected in 2 days.
    add_card(
        session, statuses, ingredients["Heavy cream"],
        created_at=bakery_time(days_ago=1, hour=7),
        moves=to_ordered, hours_between=3,
        expected_delivery_date=today + timedelta(days=2),
    )

    # 7. Ordered, overdue: delivery was expected 2 days ago.
    add_card(
        session, statuses, ingredients["Free-range eggs"],
        created_at=bakery_time(days_ago=6, hour=8),
        moves=to_ordered, hours_between=8,
        expected_delivery_date=today - timedelta(days=2),
        position=1,
    )

    # 8. Delayed, with a reason and a next action (also kept in the history note).
    reason = "Supplier out of stock"
    next_action = "Try another supplier"
    add_card(
        session, statuses, ingredients["Vanilla pods"],
        created_at=bakery_time(days_ago=8, hour=8),
        moves=to_ordered + ["Delayed"], hours_between=24,
        notes={4: f"Reason: {reason}. Next action: {next_action}."},
        delay_reason=reason, delay_next_action=next_action,
        expected_delivery_date=today + timedelta(days=2),
    )

    # 9. Restocked and paid.
    card, last_move = add_card(
        session, statuses, ingredients["Bread flour"],
        created_at=bakery_time(days_ago=7, hour=8),
        moves=to_ordered + ["Restocked"], hours_between=24,
        expected_delivery_date=today - timedelta(days=3),
    )
    paid_at = last_move + timedelta(hours=2)
    card.paid_at = paid_at
    card.paid_by = MANAGER
    session.add(
        CardEvent(card_id=card.id, action=CardAction.paid, actor=MANAGER, timestamp=paid_at)
    )

    # 10. Soft-deleted from Running low: a duplicate of card 3.
    created_at = bakery_time(days_ago=1, hour=8, minute=5)
    deleted_at = created_at + timedelta(minutes=55)
    reason = "Duplicate card, created by mistake"
    card, _ = add_card(
        session, statuses, ingredients["Granulated sugar"],
        created_at=created_at, position=2,
        deleted_at=deleted_at, deleted_by=MANAGER, deleted_reason=reason,
    )
    session.add(
        CardEvent(
            card_id=card.id,
            action=CardAction.deleted,
            actor=MANAGER,
            note=reason,
            timestamp=deleted_at,
        )
    )


def add_signoffs(session):
    """Yesterday's two reviews are signed off; today's morning review is missing."""
    yesterday = bakery_today() - timedelta(days=1)
    session.add_all(
        [
            ReviewSignOff(
                business_date=yesterday,
                session=ReviewSession.morning,
                signed_by=CHEF,
                items_reviewed=2,
                signed_at=bakery_time(days_ago=1, hour=10, minute=15),
            ),
            ReviewSignOff(
                business_date=yesterday,
                session=ReviewSession.afternoon,
                signed_by=CHEF,
                items_reviewed=1,
                signed_at=bakery_time(days_ago=1, hour=15, minute=40),
            ),
        ]
    )


if __name__ == "__main__":
    from database import engine

    try:
        seed(engine)
    except NotSQLiteError as error:
        raise SystemExit(str(error))
    print(
        "Seeded Sunrise Bakery demo data: 6 columns, 3 suppliers, 8 ingredients, "
        "10 cards (1 deleted) with history, and 2 review sign-offs."
    )
