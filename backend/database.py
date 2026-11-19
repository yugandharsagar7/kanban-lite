"""Database connection for the Kanban Lite API."""

import os
from pathlib import Path

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

# Loads the table definitions, so create_db_and_tables() knows which tables exist.
import models  # noqa: F401


# 1. Where the database lives.
# The connection string comes from the DATABASE_URL environment variable, so no
# server address or password is ever written into the code. If it isn't set,
# use a SQLite file called kanban.db next to this file (the backend folder).
BACKEND_FOLDER = Path(__file__).resolve().parent
DEFAULT_DATABASE_URL = f"sqlite:///{BACKEND_FOLDER / 'kanban.db'}"

DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


# 2. Build an engine (the object that manages connections to the database).
# Used for the app's database and by the tests, so both get the same settings.
def make_engine(url):
    """Build an engine for this connection string, with foreign-key checks on for SQLite."""
    is_sqlite = url.startswith("sqlite")
    # check_same_thread=False lets FastAPI use SQLite from more than one request.
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if is_sqlite else {},
    )
    # SQLite ignores links between tables (for example a card pointing to a
    # supplier that doesn't exist) unless each new connection switches checks on.
    if is_sqlite:

        @event.listens_for(engine, "connect")
        def turn_on_foreign_keys(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

    return engine


engine = make_engine(DATABASE_URL)


# 3. Create every table defined in models.py.
# This only creates tables that don't exist yet; it never changes existing ones.
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# 4. Give each API request its own database session, closed when the request ends.
def get_session():
    with Session(engine) as session:
        yield session
