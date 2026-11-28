# Kanban Lite

## About me
I'm a solutions architect learning Python, and I have never coded before.
Pitch explanations accordingly: plain language, no unexplained jargon. When a
new concept comes up (a decorator, a type hint, a foreign key), explain it
briefly the first time.

## Standing instructions
1. **Explain first.** Before making any change, explain in plain language what
   you are going to change, in which file, and why. Then make the change.
2. **One small change at a time.** Make a single, small change, then stop so I
   can review it. Don't bundle several changes together.
3. **Only edit the files I name.** If a task needs a change in another file, tell
   me which file and why, and wait for me to name it.
4. **Never run git commands.** No `git` of any kind (not even `status`, `diff` or
   `log`). I commit myself.
5. **No secrets or real business data in the code.** No passwords, API keys or
   tokens; those belong in a `.env` file, which is never committed. All names,
   phone numbers, addresses and prices must be made up.
6. **`docs/requirements.md` is the source of truth.** Check it before building
   anything. If my request conflicts with it, or the feature is listed under
   "Out of scope for v1", point that out before doing anything.
7. **Use `Decimal` for money and quantities, never `float`.**

## About the project
A restocking board for a fictional bakery, "Sunrise Bakery". Kitchen staff flag
ingredients that are running low, and each restock card moves across the board
until it is restocked.

All business rules (board columns, card movement rules, roles, data model and
non-functional requirements) are defined in `docs/requirements.md`, which is
the single source of truth. Don't copy those rules into this file.

- `backend/`: the Python API (FastAPI + SQLModel). `main.py` is the app,
  `models.py` defines the database tables.
- `frontend/`: the React + TypeScript board (Vite). Run from `frontend/`:
  `npm run dev` (then open http://localhost:5173), `npm test`, `npm run build`.
- `docs/requirements.md`: the v1 requirements.

Commands (run from `backend/`):
- Activate the Python environment: `source .venv/bin/activate`
- Start the API: `uvicorn main:app --reload`, then open http://127.0.0.1:8000/health
- Run tests: `pytest`
