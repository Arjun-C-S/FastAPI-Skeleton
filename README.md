# Bifrost

<p align="center">
  <img
    src="https://oyster.ignimgs.com/mediawiki/apis.ign.com/marvel-studios-cinematic-universe/7/7e/Bifrost1.jpg?width=960"
    alt="Bifröst, the rainbow bridge between worlds"
    width="480"
  />
</p>

<p align="center">
  <em>Bifröst — the bridge between worlds.</em>
</p>

In Norse myth, **Bifröst** is the burning rainbow bridge that connects Midgard (our world) to Asgard. This service is built on that idea.

## What this project is

**Bifrost** is a FastAPI service that sits between **Langfuse** and the rest of your stack.

Other services should not talk to Langfuse directly. They talk to Bifrost. Bifrost fetches prompts, serves them in a stable API shape, and keeps a local backup so prompt delivery does not die when Langfuse is slow, down, or unreachable.

| When Langfuse is… | Bifrost should… |
| --- | --- |
| Healthy | Fetch prompts from Langfuse, cache them, return them to callers |
| Slow | Serve a recent cached copy (Redis) |
| Down | Fall back to the last known-good prompts in Postgres |

Callers get prompts either way. Langfuse stays the source of truth when it is available; Bifrost is the bridge that keeps working when it is not.

The HTTP skeleton is in place (config, Redis, Postgres session, caching, errors, health). Langfuse sync and the prompt APIs are the next layer on this foundation.

## Requirements

- Git
- [uv](https://docs.astral.sh/uv/) (installs and uses Python **3.13**)
- Docker Desktop (Docker Engine + Compose v2)

System Python 3.10 is not enough. Do not use `pip` or a global interpreter.

## Setup

### 1. Clone and install

```powershell
git clone <repo-url>
cd Bifrost
uv sync --group dev
```

### 2. Create `.env`

```powershell
# PowerShell
Copy-Item .env.example .env
```

```bash
# macOS / Linux
cp .env.example .env
```

Copy `.env.example` to `.env`. Change `SECRET_KEY` before anything leaves your machine.

`DATABASE_URL` and `REDIS_URL` use `localhost` so `uv run poe dev` can reach Redis/Postgres on published ports. The API container cannot use `localhost` (that would be itself), so Compose rebuilds those two URLs from `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, and `REDIS_PORT` with the Compose service names `postgres` and `redis`.

```env
APP_NAME=Bifrost
APP_ENV=development
APP_PORT=8000

POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=bifrost
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/bifrost

SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

REDIS_PORT=6379
CACHE_TTL=300
REDIS_URL=redis://localhost:6379/0

ALLOWED_ORIGINS=["http://localhost:3000"]
DOZZLE_PORT=8080
COMPOSE_PROFILES=dev
```

`DATABASE_URL` must be set even before Postgres is running. The health endpoint does not open a database connection; Redis does get opened on startup.

### 3. Run with Docker

Docker Desktop must be running. Confirm the engine is up:

```powershell
docker info
```

If you see `dockerDesktopLinuxEngine` / `error during connect`, start Docker Desktop and wait until it is ready.

`.env` is required. Compose interpolates `APP_PORT`, `POSTGRES_*`, `REDIS_PORT`, and `DOZZLE_PORT` from it. `COMPOSE_PROFILES=dev` starts Dozzle. There are no defaults in `docker-compose.yml`.

Clear name/port clashes from earlier `docker run` containers:

```powershell
docker rm -f bifrost-api bifrost-redis bifrost-postgres bifrost-dozzle
```

Build and start the API, Redis, and Postgres:

```powershell
docker compose up --build
```

Detached:

```powershell
docker compose up --build -d
```

Same thing via Poe: `uv run poe up`.

Wait until the API is healthy:

```powershell
docker compose ps
```

`bifrost-api`, `bifrost-redis`, and `bifrost-postgres` should show `healthy` (or `running` while the healthcheck start period finishes). Then:

```powershell
# PowerShell
Invoke-RestMethod http://127.0.0.1:8000/health
```

```bash
curl http://127.0.0.1:8000/health
```

| | |
| --- | --- |
| API | http://127.0.0.1:8000 |
| Health | http://127.0.0.1:8000/health |
| Docs | http://127.0.0.1:8000/docs (`APP_ENV=development`) |
| Logs (Dozzle) | http://127.0.0.1:8080 |
| Redis | localhost:6379 (`bifrost-redis`) |
| Postgres | localhost:5432 (`bifrost-postgres`) |

Live container logs are in Dozzle at http://127.0.0.1:8080 (no login). It only starts when `COMPOSE_PROFILES=dev`. In production, omit that variable so the Dozzle service is not created.

```powershell
# still available if you want the CLI
docker compose logs -f api
```

Stop containers (keeps the Postgres volume):

```powershell
docker compose down
```

Stop and delete the Postgres volume (needed after changing the volume mount, or to reset the database):

```powershell
docker compose down -v
```

Poe equivalent of `down`: `uv run poe down`.

**If a port is already in use** (`6379`, `5432`, `8000`, or `8080`), change `REDIS_PORT`, `POSTGRES_PORT`, `APP_PORT`, or `DOZZLE_PORT` in `.env` and run `docker compose up --build` again.

**If the API exits immediately**, Redis did not become healthy in time or `.env` is incomplete. Check:

```powershell
docker compose logs api
docker compose logs redis
```

The image does not copy `.env`. Compose reads it for interpolation and injects it with `env_file`. Inside the API container, `DATABASE_URL` / `REDIS_URL` are rebuilt from `POSTGRES_*` so they use the service names `postgres` and `redis` instead of `localhost`.

### 4. Run the API on the host

Start only Redis and Postgres, then run Uvicorn locally:

```powershell
uv run poe infra
uv run poe dev
```

`poe infra` is `docker compose up -d redis postgres`. Redis must be up or the process will not start.

### 5. Install git hooks

This only works inside a Git checkout (`git clone` or `git init`).

```powershell
uv run poe pre-commit-install
```

That installs:

- **pre-commit:** Ruff lint/format, mypy
- **commit-msg:** `conventional-gitmoji` (prepends the emoji), then Commitizen (rejects non-conventional messages)

## Run on the host

For the full stack in Docker, use [Setup step 3](#3-run-with-docker).

```powershell
uv run poe dev
```

| | |
| --- | --- |
| API | http://127.0.0.1:8000 |
| Health | http://127.0.0.1:8000/health |
| Docs | http://127.0.0.1:8000/docs (`APP_ENV=development` only) |

Without reload:

```powershell
uv run poe start
```

## Commands

Defined in `pyproject.toml`. Run with `uv run poe <task>`.

| Task | What it does |
| --- | --- |
| `dev` | API with auto-reload |
| `start` | API without reload |
| `lint` | Ruff lint |
| `lint-fix` | Ruff lint + autofix |
| `format` | Ruff format |
| `format-check` | Format check only |
| `typecheck` | mypy (`app/`) |
| `check` | lint + format-check + typecheck |
| `commit` | `cz commit` using the `cz_gitmoji` adapter |
| `pre-commit-install` | Install pre-commit and commit-msg hooks |
| `infra` | `docker compose up -d redis postgres` |
| `up` | `docker compose up --build` |
| `down` | `docker compose down` |

```powershell
uv run poe --help
```

`migrate` and `revision` are also defined. They call Alembic and **fail today** — see below.

## Migrations

Alembic is a project dependency. It is not initialized.

- `alembic.ini` is empty
- there is no `alembic/` directory
- `uv run poe migrate` currently errors: `No 'script_location' key found in configuration`

When the first SQLAlchemy models are added, initialize Alembic, then create and apply migrations:

```powershell
uv run poe revision -- -m "add prompt table"
```

Review the generated file. Autogenerate is a draft, not a guarantee. Then:

```powershell
uv run poe migrate
```

Do not run those two commands until the migration tree exists.

## Layout

```text
app/
  api/v1/          # HTTP routers (to be filled)
  core/            # settings, exceptions, handlers, security
  db/              # SQLAlchemy session, Redis, cache helpers
  middleware/      # request logging
  models/          # ORM models
  schemas/         # Pydantic response/request models
  services/        # Langfuse client, fallback, prompt retrieval
Dockerfile         # production image (uv deps, non-root, uvicorn)
docker-compose.yml # api + redis + postgres
```

## Commits

Two separate pieces, both configured:

1. **`uv run poe commit`** runs `cz commit` with `[tool.commitizen] name = "cz_gitmoji"`. The adapter writes the emoji into the message, for example `✨ feat: …` / `🐛 fix: …`.
2. **`git commit -m "feat: …"`** does **not** go through Poe. After hooks are installed, the `commit-msg` hook `conventional-gitmoji` runs `gitmojify`, which prepends the emoji for a known type. Commitizen then validates the result.

```powershell
git commit -m "feat: add Langfuse prompt lookup"
# gitmojify → ✨ feat: add Langfuse prompt lookup
```

If the message already has a gitmoji, `gitmojify` leaves it alone.

Verified with the installed tools:

```text
gitmojify -m "feat: add Langfuse prompt lookup"
  → ✨ feat: add Langfuse prompt lookup

cz check --message "feat: add Langfuse prompt lookup"     # ok
cz check --message "✨ feat: add Langfuse prompt lookup"  # ok
cz check --message "updated stuff"                        # rejected
```

Plain messages without a conventional type are rejected. The full hook chain only runs after `uv run poe pre-commit-install` in a Git repository.

## Notes

- Redis must be up or the process will not start.
- `/docs` is disabled when `APP_ENV` is not `development`.
- Do not commit `.env`. `.env.example` is the template.
- Compose publishes Postgres and Redis on localhost so `uv run poe dev` can use the same `.env`.
