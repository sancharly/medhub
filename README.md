# MedHub

A medical web application built with FastAPI + React.

![CI](https://github.com/sancharly/medhub/actions/workflows/ci.yml/badge.svg)

## Quick Start

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
# API available at http://localhost:8000
# Docs at http://localhost:8000/api/v1/openapi.json
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

### Full stack with Docker Compose

```bash
cp infra/.env.example infra/.env
# Edit infra/.env with real values
docker compose -f infra/docker-compose.yml up
# App available at https://localhost (HTTPS via reverse proxy)
```

See `infra/DEPLOY.md` for production deployment instructions.

## Development

### Backend

```bash
cd backend
uv run ruff check          # lint
uv run black --check .     # format check
uv run mypy app            # type check
uv run pytest              # tests
```

### Frontend

```bash
cd frontend
npm run lint               # ESLint
npm run typecheck          # TypeScript
npm test                   # Vitest
```
