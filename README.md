# Kanban Lite

A replenishment Kanban app for a small (fictional) bakery. Each card signals
that an ingredient or supply needs restocking, and moves across the board
until it's back on the shelf.

> **Status:** v1 in progress, week [2] of a 13-week build.
> I'm building this to get hands-on with the full stack and Azure, from
> requirements to running cloud code.

## What it does (v1)

- Board with columns for each replenishment stage, e.g. [Needs reorder ->
  Ordered -> Received -> Stocked]
- Cards for each item: [name, quantity, supplier, due date]
- WIP limits per column, with a warning when a column is over its limit
- A required reason when a card is blocked
- Card history: who moved it, when, from where to where
- Filters

## Tech stack

| Layer | Now | Planned |
| --- | --- | --- |
| Back end | Python, FastAPI, SQLModel | Azure Container Apps |
| Front end | React, TypeScript, Vite, dnd-kit | Azure Static Web Apps |
| Database | SQLite (local) | Azure SQL |
| Infrastructure | - | Bicep |
| CI/CD | - | GitHub Actions with OIDC |
| Sign-in and secrets | - | Entra ID, managed identity, Key Vault |
| Monitoring | - | Application Insights |
| AI | - | Shift summary using Azure OpenAI |

## Roadmap

- [ ] v1 running locally with tests
- [ ] Containerized with Docker
- [ ] Azure infrastructure defined in Bicep
- [ ] CI/CD pipeline
- [ ] Entra ID sign-in, no passwords anywhere
- [ ] Monitoring and alerts
- [ ] AI-generated restocking summary

## Run it locally (macOS)

```bash
# Back end
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
# API docs: http://127.0.0.1:8000/docs
```

[Front end steps will be added when the front end is built.]

## Docs

- [Requirements](docs/requirements.md)
- [Learning log](docs/learning-log.md): what I built each session and what I learned