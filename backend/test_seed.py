"""Tests for seed.py. Each test uses a fresh in-memory database, never kanban.db."""

import pytest
from sqlmodel import Session, select

from database import make_engine
from models import CardAction, CardEvent, RestockCard, RestockStatus, Role
from seed import seed


@pytest.fixture
def engine():
    """A fresh, empty in-memory database engine, with the same settings as the app."""
    engine = make_engine("sqlite://")
    yield engine
    engine.dispose()


def test_seed_runs_twice_without_errors(engine):
    seed(engine)
    seed(engine)  # the second run must start clean, not add a second copy
    with Session(engine) as session:
        assert len(session.exec(select(RestockCard)).all()) == 10


def test_six_statuses_are_in_board_order(engine):
    seed(engine)
    with Session(engine) as session:
        statuses = session.exec(select(RestockStatus).order_by(RestockStatus.position)).all()
    # Written out here on purpose, copied from docs/requirements.md, so the test
    # doesn't just compare seed.py with itself.
    assert [status.name for status in statuses] == [
        "Running low",
        "Manager review",
        "Owner review",
        "Ordered",
        "Restocked",
        "Delayed",
    ]


def test_every_card_history_ends_at_its_current_status(engine):
    seed(engine)
    with Session(engine) as session:
        cards = session.exec(select(RestockCard)).all()
        for card in cards:
            # Only "created" and "moved" put a card in a column;
            # "paid" and "deleted" don't change where it is.
            last_placement = session.exec(
                select(CardEvent)
                .where(CardEvent.card_id == card.id)
                .where(CardEvent.action.in_([CardAction.created, CardAction.moved]))
                .order_by(CardEvent.timestamp.desc(), CardEvent.id.desc())
            ).first()
            assert last_placement is not None, f"card {card.id} has no history"
            assert last_placement.to_status_id == card.status_id, (
                f"card {card.id}'s history ends in a different column"
            )


def test_each_status_has_its_role_and_final_flag(engine):
    seed(engine)
    with Session(engine) as session:
        statuses = session.exec(select(RestockStatus).order_by(RestockStatus.position)).all()
    # Written out from "Board columns" in docs/requirements.md.
    assert [(s.name, s.responsible_role, s.is_final) for s in statuses] == [
        ("Running low", Role.head_chef, False),
        ("Manager review", Role.bakery_manager, False),
        ("Owner review", Role.owner, False),
        ("Ordered", Role.bakery_manager, False),
        ("Restocked", None, True),
        ("Delayed", Role.bakery_manager, False),
    ]
