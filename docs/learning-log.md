# Learning log

What I built each session, the ideas that mattered, the decisions I made and why,
and what went wrong. Newest first. The "In my own words" line in each entry is
mine to fill in.

## 2026-11-21 to 22: Seed data, first data endpoints, accountability

**Built:** `backend/settings.py` and `backend/seed.py` with tests (with Claude Code).
`GET /statuses` and `GET /board`, plus `backend/schemas.py` (typed myself).
Requirements for overdue cards, whose turn it is, final status and completion.

**Key ideas**
- The seed is rerunnable: it drops and recreates every table, so it also rebuilds
  the database after a model change. A safety catch refuses anything but SQLite.
- The bakery's time zone (America/New_York) is a business rule, not the server's
  clock. Cloud servers run in UTC, so "today" comes from `bakery_today()`.
- One path builds both a card and its history, so they can't disagree.
- `flush()` gives rows their ids; one `commit()` at the end saves everything or
  nothing. That's a transaction.
- A test must check against an independent source, not the code's own values.
- Never show secrets such as `DATABASE_URL` in error messages or logs.
- A JOIN combines tables through their foreign keys.
- `Depends(get_session)` is dependency injection: FastAPI supplies the session.
- Response models (no `table=True`) shape the API's answer: nested, only what
  the screen needs, plus calculated values like `estimated_total`.
- The API sends `Decimal` as text so values arrive exactly; the screen rounds.
- Sort by position, then id, so ties always come back in the same order.

**Design decisions (mine)**
- Responsible versus accountable: each column has a role whose turn it is, but
  the Bakery Manager is accountable from owner approval until the card is complete.
- Restocked is a final status with no next step forward, but a card is only
  complete when it is restocked and paid. Unpaid restocked cards show
  "Awaiting payment (Bakery Manager)".
- A restocked card can move back to Ordered, with a note, for a wrong delivery.
- Overdue means past the expected delivery date and still in Ordered or Delayed.

**In my own words:**

## 2026-11-19: Model tests

**Built:** `backend/test_models.py` (with Claude Code): 30 test runs covering every
database rule, all passing in 0.24 seconds. `database.py` now builds its engine
with `make_engine()`, which the tests use too.

**Key ideas**
- A test is a small saved program that checks one rule. `pytest -v` reruns them
  all and lists each as PASSED or FAILED.
- A fixture is setup that pytest runs before a test that asks for it. Here, each
  test gets a fresh in-memory database, so tests never touch `kanban.db`.
- Tests must use the same setup as the app. One shared `make_engine()` function
  means the tests can't run without the foreign-key checks the app uses.
- `pytest.raises(IntegrityError)` passes only if the database refuses a bad row.
- `@pytest.mark.parametrize` runs one test with several inputs.
- A regression test stops something already fixed from breaking again (the
  3- and 4-decimal storage test).
- When `models.py` changes, delete `kanban.db` and recreate it: `create_all`
  never updates existing tables.

**What went wrong:** four stray spaces at the start of `database.py` broke the file,
and that broken version was committed. Lesson: check before every commit
(`pytest`, or `python -c "import database, models"`).

**In my own words:**

## 2026-11-18: Database setup

**Built:** `backend/database.py` (with Claude Code), and the first real database,
`backend/kanban.db`, with all six tables.

**Key ideas**
- The connection string comes from the `DATABASE_URL` environment variable, with
  a local SQLite file as the default. The same code runs on my laptop and in
  Azure; no address or password is in the code.
- SQLite leaves foreign-key checks off by default. `database.py` switches them on
  for every new connection (`PRAGMA foreign_keys = ON`).
- Some lines look unused but have a job: `import models` tells SQLModel which
  tables exist. Without it, no tables would be created, and no error shown.
- `create_all` only creates missing tables. It never changes existing ones.
- The database file is ignored by Git (`*.db`), so local data never reaches GitHub.

**In my own words:**

## 2026-11-17: Model review, money storage, database rules

**Built:** decision record `docs/decisions/0001-money-storage.md`, payment rules in
the requirements, and six groups of rules in `backend/models.py` (with Claude Code).

**Key ideas**
- SQLite has no exact decimal type and stores `Decimal` as a float. Decision: keep
  `Decimal`, do all money maths in Python in v1, use exact `DECIMAL` on Azure SQL.
- Quantities keep 3 decimal places, unit prices 4. The database silently rounds
  extra decimals, so the API's input models must reject them with a clear message.
- Defense in depth: Enums protect the code, check constraints protect the database.
  An Enum alone did not stop SQLite saving "bananas".
- Unique constraint: one column name and position; one sign-off per date and
  session (a composite unique constraint).
- Check constraints: no negative prices, no zero quantities, delete fields all
  filled or all empty, paid fields together, paid cards can't be deleted.
- Three-valued logic: in SQL, comparing NULL gives "unknown", and a check that is
  "unknown" lets the row through. So rules need explicit `IS NOT NULL` checks.
- Rules that depend on which column a card is in (mark paid only in Ordered or
  later, no moving back once paid) belong in the API, not the database.
- Principle: once money has gone out, the app never hides or undoes that fact.

**What went wrong:** the same commit message used twice. Not fixed, because
rewriting pushed history isn't worth the risk. Each commit should say what it changed.

**In my own words:**

## 2026-11-16: The data model, first Claude Code session

**Built:** six models in `backend/models.py` (typed myself): Supplier, Ingredient,
RestockStatus, RestockCard, CardEvent, ReviewSignOff. Plus `CLAUDE.md`.

**Key ideas**
- A model is a Python description of one table. A foreign key (`supplier_id`)
  points to a row in another table, so each fact lives in one place (normalization).
- `Decimal`, not `float`, for money: `0.1 + 0.2` as floats is `0.30000000000000004`.
- `default_factory` runs a function for each new row, so every card gets its own
  creation time. Times are stored in UTC.
- Avoid names that clash: `COLUMN` is a SQL reserved word, and `date` is already a
  Python type. Hence `RestockStatus` and `business_date`.

**Design decisions (mine)**
- Status, not column: name things in the business's language.
- One restock card per order, not a status on the ingredient. That allows several
  orders per item and keeps history for reports.
- Price and supplier snapshot on each card, so later price changes don't rewrite
  past orders.
- Columns named for whose turn it is: Running low, Manager review, Owner review,
  Ordered, Restocked, plus Delayed. Moving forward is approval.
- One step at a time; moving back needs a note; no reject button.
- Price editable only in Manager review. Soft delete by the bakery manager only,
  with a reason.

**What went wrong:** rushed Claude Code to use up my usage before a reset, couldn't
read its answers in Terminal, and undid its changes with `git restore`. Lesson:
go at my own pace, and read every change before accepting it.

**In my own words:**

## 2026-11-15: Requirements, first commit, first API

**Built:** `docs/requirements.md`, `.gitignore`, the private GitHub repo, the
Python virtual environment, and `backend/main.py` with a working `/health`.

**Key ideas**
- Git saves snapshots (commits) locally; GitHub holds a copy (a remote). Staging
  (`git add`) then committing (`git commit`), then `git push`.
- `.gitignore` keeps secrets, local data and downloaded libraries out of Git.
- A virtual environment gives the project its own Python and libraries.
- FastAPI turns Python functions into web addresses and builds the `/docs` page.

**Design decisions (mine)**
- Replenishment Kanban for a fictional bakery, deliberately different from my
  employer's app. Written fresh, not adapted from my work requirements.
- A chef review sign-off with a missed-review alert instead of a WIP limit.

**In my own words:**

## 2026-11-14: Machine setup

**Built:** GitHub account with two-factor sign-in; installed Git, Homebrew,
Python 3.12, Node.js, VS Code with extensions, and Claude Code.

**Key ideas**
- PATH is the list of folders Terminal searches for commands. "Command not found"
  usually means the tool is installed but its folder isn't on the PATH.
- Each installer has its own job: Homebrew for programs, `code` for VS Code
  extensions, pip for Python libraries, npm for JavaScript libraries.

**In my own words:**
