"""Tests for the API endpoints in main.py.

Every test uses a fresh in-memory database. Two things keep kanban.db safe:
- endpoints get the test database through app.dependency_overrides, and
- the app's start-up hook is swapped (with monkeypatch) for one that creates
  the tables in the test database.
All data comes from seed.py, so it is all made up.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, select

import main
from database import get_session, make_engine
from models import Ingredient, RestockCard, RestockStatus, Supplier
from seed import seed


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def engine():
    """One shared in-memory database (StaticPool), with the app's foreign-key setting."""
    engine = make_engine("sqlite://", poolclass=StaticPool)
    yield engine
    engine.dispose()


@pytest.fixture
def client(engine, monkeypatch):
    """The app, running against the test database. Tables exist but are empty."""

    def test_session():
        with Session(engine) as session:
            yield session

    # monkeypatch swaps something for one test and puts it back afterwards.
    # Here: the start-up hook creates tables in the test database, never kanban.db.
    monkeypatch.setattr(main, "create_db_and_tables", lambda: SQLModel.metadata.create_all(engine))
    main.app.dependency_overrides[get_session] = test_session
    with TestClient(main.app) as client:  # "with" runs the (swapped) start-up hook
        yield client
    main.app.dependency_overrides.clear()


@pytest.fixture
def seeded_client(engine, client):
    """The app, with the full Sunrise Bakery demo data from seed.py."""
    seed(engine)
    return client


def get_board(client):
    response = client.get("/board")
    assert response.status_code == 200
    return response.json()


def column(board, name):
    """One column of the board, found by its name."""
    return next(col for col in board if col["name"] == name)


def card(board, column_name, ingredient):
    """The card for this ingredient in this column."""
    return next(c for c in column(board, column_name)["cards"] if c["ingredient"] == ingredient)


def all_cards(board):
    return [c for col in board for c in col["cards"]]


def find_card(engine, column_name, ingredient_name):
    """Look up a card's id in the database, by its column and ingredient."""
    with Session(engine) as session:
        return session.exec(
            select(RestockCard.id)
            .join(RestockStatus, RestockCard.status_id == RestockStatus.id)
            .join(Ingredient, RestockCard.ingredient_id == Ingredient.id)
            .where(RestockStatus.name == column_name, Ingredient.name == ingredient_name)
        ).one()


def update_card(engine, card_id, **changes):
    """Change fields on one card in the test database, then save."""
    with Session(engine) as session:
        row = session.get(RestockCard, card_id)
        for field, value in changes.items():
            setattr(row, field, value)
        session.add(row)
        session.commit()


# ---------------------------------------------------------------------------
# /health and /statuses
# ---------------------------------------------------------------------------


def test_health_says_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_statuses_come_in_board_order_with_their_roles(seeded_client):
    response = seeded_client.get("/statuses")
    assert response.status_code == 200
    # Written out from "Board columns" in docs/requirements.md.
    assert [
        (s["name"], s["responsible_role"], s["responsible_role_name"], s["is_final"])
        for s in response.json()
    ] == [
        ("Running low", "head_chef", "Head Chef", False),
        ("Manager review", "bakery_manager", "Bakery Manager", False),
        ("Owner review", "owner", "Owner", False),
        ("Ordered", "bakery_manager", "Bakery Manager", False),
        ("Restocked", None, None, True),
        ("Delayed", "bakery_manager", "Bakery Manager", False),
    ]


# ---------------------------------------------------------------------------
# /board: columns and cards
# ---------------------------------------------------------------------------


def test_board_has_six_columns_with_the_seeded_cards(seeded_client):
    board = get_board(seeded_client)
    assert [(col["name"], len(col["cards"])) for col in board] == [
        ("Running low", 2),
        ("Manager review", 2),
        ("Owner review", 1),
        ("Ordered", 2),
        ("Restocked", 1),
        ("Delayed", 1),
    ]


def test_deleted_card_is_not_on_the_board(seeded_client, engine):
    with Session(engine) as session:
        deleted_id = session.exec(
            select(RestockCard.id).where(RestockCard.deleted_at.is_not(None))
        ).one()
    board = get_board(seeded_client)
    assert deleted_id not in [c["id"] for c in all_cards(board)]


def test_card_keeps_its_own_price_and_supplier(seeded_client, engine):
    # Change the ingredient's price and supplier after the card was created.
    with Session(engine) as session:
        saffron = session.exec(select(Ingredient).where(Ingredient.name == "Saffron")).one()
        other_supplier = session.exec(
            select(Supplier).where(Supplier.name == "Golden Mill Supplies")
        ).one()
        saffron.price_per_unit = Decimal("9999.0000")
        saffron.supplier_id = other_supplier.id
        session.add(saffron)
        session.commit()

    saffron_card = card(get_board(seeded_client), "Manager review", "Saffron")
    assert Decimal(saffron_card["unit_price"]) == Decimal("4250.0000")
    assert saffron_card["supplier"] == "Orchard Spice Traders"


def test_estimated_total_is_exact(seeded_client):
    saffron_card = card(get_board(seeded_client), "Manager review", "Saffron")
    # 0.125 kg x 4250.0000 per kg, calculated in Python, no rounding.
    assert Decimal(saffron_card["estimated_total"]) == Decimal("531.25")


def test_only_the_paid_card_is_marked_paid(seeded_client):
    board = get_board(seeded_client)
    paid = [(col["name"], c["ingredient"]) for col in board for c in col["cards"] if c["is_paid"]]
    assert paid == [("Restocked", "Bread flour")]


def test_cards_in_a_column_follow_position_then_id(seeded_client, engine):
    cream = find_card(engine, "Ordered", "Heavy cream")
    eggs = find_card(engine, "Ordered", "Free-range eggs")

    # Different positions: the lower position comes first.
    update_card(engine, eggs, position=0)
    update_card(engine, cream, position=1)
    assert [c["id"] for c in column(get_board(seeded_client), "Ordered")["cards"]] == [eggs, cream]

    # Same position: the lower id comes first, every time.
    update_card(engine, eggs, position=3)
    update_card(engine, cream, position=3)
    for _ in range(3):
        ids = [c["id"] for c in column(get_board(seeded_client), "Ordered")["cards"]]
        assert ids == sorted([eggs, cream])


def test_empty_database_gives_empty_lists(client):
    # No seed: the tables exist only because the start-up hook created them.
    assert client.get("/statuses").json() == []
    assert client.get("/board").json() == []


# ---------------------------------------------------------------------------
# Overdue
# ---------------------------------------------------------------------------

FIXED_TODAY = date(2026, 11, 20)


@pytest.mark.parametrize(
    "column_name, due_in_days, expected",
    [
        ("Ordered", -1, True),
        ("Ordered", 0, False),
        ("Ordered", 1, False),
        ("Delayed", -1, True),
        ("Restocked", -1, False),
        ("Running low", -1, False),
        ("Ordered", None, False),
    ],
    ids=[
        "ordered, due yesterday",
        "ordered, due today",
        "ordered, due tomorrow",
        "delayed, due yesterday",
        "restocked, due yesterday",
        "running low, due yesterday",
        "ordered, no date",
    ],
)
def test_overdue_rule(column_name, due_in_days, expected):
    due = None if due_in_days is None else FIXED_TODAY + timedelta(days=due_in_days)
    status = RestockStatus(name=column_name, position=1)
    restock_card = RestockCard(expected_delivery_date=due)
    assert main.is_overdue(restock_card, status, FIXED_TODAY) is expected


def test_board_marks_overdue_cards(seeded_client):
    board = get_board(seeded_client)
    assert card(board, "Ordered", "Free-range eggs")["is_overdue"] is True  # due 2 days ago
    assert card(board, "Ordered", "Heavy cream")["is_overdue"] is False  # due in 2 days
    assert card(board, "Restocked", "Bread flour")["is_overdue"] is False  # already delivered
    assert card(board, "Delayed", "Vanilla pods")["is_overdue"] is False  # due in 2 days


def test_overdue_uses_the_bakery_date(seeded_client, monkeypatch):
    eggs_due = date.fromisoformat(
        card(get_board(seeded_client), "Ordered", "Free-range eggs")["expected_delivery_date"]
    )

    # On the due date itself, the eggs are not overdue yet ...
    monkeypatch.setattr(main, "bakery_today", lambda: eggs_due)
    assert card(get_board(seeded_client), "Ordered", "Free-range eggs")["is_overdue"] is False

    # ... and the day after, they are.
    monkeypatch.setattr(main, "bakery_today", lambda: eggs_due + timedelta(days=1))
    assert card(get_board(seeded_client), "Ordered", "Free-range eggs")["is_overdue"] is True


def test_overdue_columns_exist(seeded_client):
    # If a column were renamed, overdue marks would silently stop. This catches it.
    names = {s["name"] for s in seeded_client.get("/statuses").json()}
    assert main.OVERDUE_COLUMNS <= names  # <= means "every one of these is in names"


# ---------------------------------------------------------------------------
# Delay details and awaiting payment
# ---------------------------------------------------------------------------


def test_delayed_card_shows_reason_and_next_action(seeded_client):
    board = get_board(seeded_client)
    vanilla = card(board, "Delayed", "Vanilla pods")
    assert vanilla["delay_reason"] == "Supplier out of stock"
    assert vanilla["delay_next_action"] == "Try another supplier"
    for other in all_cards(board):
        if other["id"] != vanilla["id"]:
            assert other["delay_reason"] is None
            assert other["delay_next_action"] is None


def test_unpaid_restocked_card_is_awaiting_payment(seeded_client, engine):
    restocked = find_card(engine, "Restocked", "Bread flour")
    update_card(engine, restocked, paid_at=None, paid_by=None)

    bread = card(get_board(seeded_client), "Restocked", "Bread flour")
    assert bread["is_paid"] is False
    assert bread["awaiting_payment"] is True


def test_paid_restocked_card_is_not_awaiting_payment(seeded_client):
    board = get_board(seeded_client)
    assert card(board, "Restocked", "Bread flour")["awaiting_payment"] is False
    # Most other cards are unpaid too, but they aren't in Restocked, so none waits for payment.
    assert [c["ingredient"] for c in all_cards(board) if c["awaiting_payment"]] == []
