from fastapi import Depends, FastAPI
from sqlmodel import Session, select

from database import get_session
from models import RestockStatus
app = FastAPI()

@app.get("/health")
def health():
    return{"status": "ok"}

@app.get("/statuses")
def list_statuses(session: Session = Depends(get_session)):
    query = select(RestockStatus).order_by(RestockStatus.position)
    return session.exec(query).all()