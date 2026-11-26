from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlmodel import Session, select
from fastapi.middleware.cors import CORSMiddleware

from database import create_db_and_tables, get_session
from models import Ingredient, RestockCard, RestockStatus, Supplier
from schemas import CardOut, ColumnOut, StatusOut
from settings import bakery_today
from settings import FRONTEND_ORIGINS

# Columns where a late delivery counts as overdue (docs/requirements.md, "Board display").
OVERDUE_COLUMNS = {"Ordered", "Delayed"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the app starts: create any tables that don't exist yet."""
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


def is_overdue(card, status, today):
    """Expected delivery date is before the bakery's today, in Ordered or Delayed."""
    return (
        status.name in OVERDUE_COLUMNS
        and card.expected_delivery_date is not None
        and card.expected_delivery_date < today
    )


def is_awaiting_payment(card, status):
    """In the final column (Restocked) but not marked paid yet."""
    return status.is_final and card.paid_at is None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/statuses", response_model=list[StatusOut])
def list_statuses(session: Session = Depends(get_session)):
    query = select(RestockStatus).order_by(RestockStatus.position)
    return session.exec(query).all()


@app.get("/board", response_model=list[ColumnOut])
def get_board(session: Session = Depends(get_session)):
    statuses = session.exec(select(RestockStatus).order_by(RestockStatus.position)).all()
    ingredients = {i.id: i for i in session.exec(select(Ingredient)).all()}
    suppliers = {s.id: s for s in session.exec(select(Supplier)).all()}
    cards = session.exec(
        select(RestockCard)
        .where(RestockCard.deleted_at.is_(None))
        .order_by(RestockCard.position, RestockCard.id)
    ).all()

    today = bakery_today()
    board = []
    for status in statuses:
        column_cards = []
        for card in cards:
            if card.status_id == status.id:
                ingredient = ingredients[card.ingredient_id]
                column_cards.append(
                    CardOut(
                        id=card.id,
                        ingredient=ingredient.name,
                        unit=ingredient.unit,
                        quantity=card.quantity,
                        unit_price=card.unit_price,
                        estimated_total=card.quantity * card.unit_price,
                        supplier=suppliers[card.supplier_id].name,
                        expected_delivery_date=card.expected_delivery_date,
                        is_paid=card.paid_at is not None,
                        delay_reason=card.delay_reason,
                        delay_next_action=card.delay_next_action,
                        is_overdue=is_overdue(card, status, today),
                        awaiting_payment=is_awaiting_payment(card, status),
                    )
                )
        board.append(
            ColumnOut(
                id=status.id,
                name=status.name,
                position=status.position,
                responsible_role=status.responsible_role,
                is_final=status.is_final,
                cards=column_cards,
            )
        )
    return board