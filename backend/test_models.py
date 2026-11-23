"""Tests for the database rules in models.py.

Every test gets a brand-new, empty, in-memory database (see the `session`
fixture), so the tests never touch kanban.db and can't affect each other.
All names, phone numbers and addresses are made up.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from database import make_engine
from models import (
    CardAction,
    CardEvent,
    Ingredient,
    RestockCard,
    RestockStatus,
    ReviewSession,
    ReviewSignOff,
    Role,
    Supplier,
    Unit,
)

# A made-up moment in time, used wherever a test needs a date and time.
WHEN = datetime(2026, 11, 17, 9, 30, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def session():
    """A fresh, empty in-memory database, with the same settings as the app."""
    engine = make_engine("sqlite://")  # "sqlite://" = in memory, no file
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session  # the test runs here
    engine.dispose()  # throw the database away afterwards


@pytest.fixture
def saved_basics(session):
    """One supplier, ingredient and column, saved so cards have something to link to."""
    supplier = save(
        session,
        Supplier(name="Golden Mill Supplies", phone="000 0000 0001", address="1 Example Lane"),
    )
    ingredient = save(
        session,
        Ingredient(
            name="Bread flour",
            unit=Unit.kg,
            price_per_unit=Decimal("1.2500"),
            regular_restock_qty=Decimal("25"),
            usual_delivery_days=2,
            supplier_id=supplier.id,
        ),
    )
    status = save(
        session,
        RestockStatus(name="Running low", position=1, responsible_role=Role.head_chef),
    )
    # A dictionary: a set of labelled items, looked up by label, e.g. basics["status"].
    return {"supplier": supplier, "ingredient": ingredient, "status": status}


def save(session, row):
    """Save one row and return it."""
    session.add(row)
    session.commit()
    return row


def make_card(basics, **changes):
    """A valid restock card. Pass changes to break one field, e.g. quantity=Decimal("0").

    **changes collects any named inputs (like quantity=...) into a dictionary.
    """
    values = {
        "ingredient_id": basics["ingredient"].id,
        "status_id": basics["status"].id,
        "supplier_id": basics["supplier"].id,
        "quantity": Decimal("10"),
        "unit_price": Decimal("1.2500"),
    }
    values.update(changes)
    return RestockCard(**values)


def make_signoff(**changes):
    """A valid review sign-off, with optional changes."""
    values = {
        "business_date": date(2026, 11, 17),
        "session": ReviewSession.morning,
        "signed_by": "Chef Sam",
        "items_reviewed": 3,
    }
    values.update(changes)
    return ReviewSignOff(**values)


def run_sql(session, sql, **values):
    """Run raw SQL, so a value reaches the database without Python checking it first."""
    session.exec(text(sql).bindparams(**values))
    session.commit()


# ---------------------------------------------------------------------------
# Sanity check: good rows must be accepted
# ---------------------------------------------------------------------------


def test_valid_rows_are_accepted(session, saved_basics):
    card = save(session, make_card(saved_basics))
    save(session, make_card(saved_basics, paid_at=WHEN, paid_by="Manager Alex"))
    save(
        session,
        make_card(
            saved_basics,
            deleted_at=WHEN,
            deleted_by="Manager Alex",
            deleted_reason="Created by mistake",
        ),
    )
    save(session, make_signoff())
    save(
        session,
        CardEvent(card_id=card.id, action=CardAction.created, to_status_id=card.status_id, actor="Kitchen Jo"),
    )
    save(session, RestockStatus(name="Restocked", position=5, is_final=True))


# ---------------------------------------------------------------------------
# Fixed lists (enums)
# ---------------------------------------------------------------------------


def test_unknown_unit_is_rejected(session, saved_basics):
    with pytest.raises(IntegrityError):
        run_sql(
            session,
            "INSERT INTO ingredient (name, unit, price_per_unit, regular_restock_qty,"
            " usual_delivery_days, supplier_id)"
            " VALUES ('Mystery fruit', 'bananas', 1, 1, 1, :supplier_id)",
            supplier_id=saved_basics["supplier"].id,
        )


def test_unknown_review_session_is_rejected(session):
    with pytest.raises(IntegrityError):
        run_sql(
            session,
            "INSERT INTO reviewsignoff (business_date, session, signed_by, items_reviewed, signed_at)"
            " VALUES ('2026-11-17', 'Morning ', 'Chef Sam', 0, '2026-11-17 09:30:00')",
        )


def test_unknown_role_is_rejected(session):
    with pytest.raises(IntegrityError):
        run_sql(
            session,
            "INSERT INTO restockstatus (name, position, responsible_role, is_final)"
            " VALUES ('Tasting', 7, 'Bakery Manager', 0)",
        )


def test_every_role_has_a_display_name():
    assert {role: role.display_name for role in Role} == {
        Role.kitchen_assistant: "Kitchen Assistant",
        Role.head_chef: "Head Chef",
        Role.bakery_manager: "Bakery Manager",
        Role.owner: "Owner",
    }


def test_unknown_card_action_is_rejected(session, saved_basics):
    card = save(session, make_card(saved_basics))
    with pytest.raises(IntegrityError):
        run_sql(
            session,
            "INSERT INTO cardevent (card_id, action, actor, timestamp)"
            " VALUES (:card_id, 'moev', 'Chef Sam', '2026-11-17 09:30:00')",
            card_id=card.id,
        )


# ---------------------------------------------------------------------------
# Unique rules
# ---------------------------------------------------------------------------


def test_duplicate_column_name_is_rejected(session):
    save(session, RestockStatus(name="Ordered", position=4, responsible_role=Role.bakery_manager))
    with pytest.raises(IntegrityError):
        save(session, RestockStatus(name="Ordered", position=9, responsible_role=Role.bakery_manager))


def test_duplicate_column_position_is_rejected(session):
    save(session, RestockStatus(name="Ordered", position=4, responsible_role=Role.bakery_manager))
    with pytest.raises(IntegrityError):
        save(session, RestockStatus(name="Restocked", position=4, is_final=True))


def test_status_that_is_not_final_needs_a_role(session):
    with pytest.raises(IntegrityError):
        save(session, RestockStatus(name="Ordered", position=4, is_final=False))


def test_final_status_cannot_have_a_role(session):
    with pytest.raises(IntegrityError):
        save(
            session,
            RestockStatus(
                name="Restocked", position=5, is_final=True, responsible_role=Role.bakery_manager
            ),
        )


def test_second_signoff_for_same_date_and_session_is_rejected(session):
    save(session, make_signoff())
    save(session, make_signoff(session=ReviewSession.afternoon))  # same date, other session: fine
    with pytest.raises(IntegrityError):
        save(session, make_signoff(signed_by="Chef Robin"))


# ---------------------------------------------------------------------------
# Minimum values
# ---------------------------------------------------------------------------


def test_negative_ingredient_price_is_rejected(session, saved_basics):
    ingredient = saved_basics["ingredient"]
    ingredient.price_per_unit = Decimal("-5")
    with pytest.raises(IntegrityError):
        save(session, ingredient)


def test_zero_restock_quantity_is_rejected(session, saved_basics):
    ingredient = saved_basics["ingredient"]
    ingredient.regular_restock_qty = Decimal("0")
    with pytest.raises(IntegrityError):
        save(session, ingredient)


def test_negative_delivery_days_is_rejected(session, saved_basics):
    ingredient = saved_basics["ingredient"]
    ingredient.usual_delivery_days = -1
    with pytest.raises(IntegrityError):
        save(session, ingredient)


def test_zero_card_quantity_is_rejected(session, saved_basics):
    with pytest.raises(IntegrityError):
        save(session, make_card(saved_basics, quantity=Decimal("0")))


def test_negative_card_price_is_rejected(session, saved_basics):
    with pytest.raises(IntegrityError):
        save(session, make_card(saved_basics, unit_price=Decimal("-1")))


def test_negative_items_reviewed_is_rejected(session):
    with pytest.raises(IntegrityError):
        save(session, make_signoff(items_reviewed=-1))


# ---------------------------------------------------------------------------
# Delete and payment fields
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "deleted_at, deleted_by, deleted_reason",
    [
        (WHEN, None, None),
        (WHEN, "Manager Alex", None),
        (WHEN, None, "Created by mistake"),
        (WHEN, "Manager Alex", "   "),
        (None, None, "Created by mistake"),
    ],
    ids=["date only", "no reason", "no name", "blank reason", "reason without date"],
)
def test_incomplete_delete_is_rejected(session, saved_basics, deleted_at, deleted_by, deleted_reason):
    card = make_card(
        saved_basics,
        deleted_at=deleted_at,
        deleted_by=deleted_by,
        deleted_reason=deleted_reason,
    )
    with pytest.raises(IntegrityError):
        save(session, card)


@pytest.mark.parametrize(
    "paid_at, paid_by",
    [
        (WHEN, None),
        (WHEN, "  "),
        (None, "Manager Alex"),
    ],
    ids=["date only", "blank name", "name without date"],
)
def test_incomplete_payment_is_rejected(session, saved_basics, paid_at, paid_by):
    with pytest.raises(IntegrityError):
        save(session, make_card(saved_basics, paid_at=paid_at, paid_by=paid_by))


def test_paid_card_cannot_be_deleted(session, saved_basics):
    card = make_card(
        saved_basics,
        paid_at=WHEN,
        paid_by="Manager Alex",
        deleted_at=WHEN,
        deleted_by="Manager Alex",
        deleted_reason="Created by mistake",
    )
    with pytest.raises(IntegrityError):
        save(session, card)


# ---------------------------------------------------------------------------
# Links between tables (foreign keys)
# ---------------------------------------------------------------------------


def make_valid_row(kind, session, basics):
    """A valid row of the given kind, ready to have one link broken."""
    if kind == "ingredient":
        return Ingredient(
            name="Caster sugar",
            unit=Unit.kg,
            price_per_unit=Decimal("0.9000"),
            regular_restock_qty=Decimal("10"),
            usual_delivery_days=3,
            supplier_id=basics["supplier"].id,
        )
    if kind == "card":
        return make_card(basics)
    if kind == "event":
        card = save(session, make_card(basics))
        return CardEvent(
            card_id=card.id,
            action=CardAction.moved,
            from_status_id=basics["status"].id,
            to_status_id=basics["status"].id,
            actor="Chef Sam",
        )
    raise ValueError(f"unknown kind: {kind}")


@pytest.mark.parametrize(
    "kind, link",
    [
        ("ingredient", "supplier_id"),
        ("card", "ingredient_id"),
        ("card", "status_id"),
        ("card", "supplier_id"),
        ("event", "card_id"),
        ("event", "from_status_id"),
        ("event", "to_status_id"),
    ],
)
def test_link_to_missing_row_is_rejected(session, saved_basics, kind, link):
    row = make_valid_row(kind, session, saved_basics)
    setattr(row, link, 999)  # setattr sets a field by its name; nothing has id 999
    with pytest.raises(IntegrityError):
        save(session, row)


# ---------------------------------------------------------------------------
# Decimal places (storage, not a rejecting rule)
# ---------------------------------------------------------------------------


def test_quantity_and_price_keep_their_decimal_places(session, saved_basics):
    card = save(
        session,
        make_card(saved_basics, quantity=Decimal("0.125"), unit_price=Decimal("12.3456")),
    )
    session.refresh(card)  # read the values back from the database
    assert card.quantity == Decimal("0.125")
    assert card.unit_price == Decimal("12.3456")
