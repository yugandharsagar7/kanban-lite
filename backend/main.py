from fastapi import Depends, FastAPI
from sqlmodel import Session, select

from database import get_session
from models import Ingredient, RestockCard, RestockStatus, Supplier
from schemas import CardOut, ColumnOut
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/statuses")
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
                    )
                )
        board.append(
            ColumnOut(id=status.id, name=status.name, position=status.position, cards=column_cards)
        )
    return board