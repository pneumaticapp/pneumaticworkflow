# Backend — Django REST API

## Stack

- Python 3.7.5+, Django 2.2, Django REST Framework 3.13.1
- PostgreSQL 15 (primary + optional replica)
- Redis 6.2.6 (caching, sessions, channels, auth tokens)
- Celery 4.4.7 + RabbitMQ (async tasks)
- Django Channels 3.0.2 + Daphne/Uvicorn (WebSockets)
- Poetry 1.5.1 (dependency management)

## Project Structure

All Django apps live under `src/`:

| App | Purpose |
|-----|---------|
| `accounts` | Users, tenants, billing plans, invitations, roles |
| `authentication` | JWT, Bearer tokens, SSO (Google, Microsoft, Auth0, Okta) |
| `processes` | Core engine: templates, workflows, tasks, checklists, comments |
| `notifications` | Email (Customer.io/SMTP), push (Firebase), WebSocket, digests |
| `webhooks` | Incoming/outgoing webhooks, event buffers |
| `payment` | Stripe subscriptions and billing |
| `ai` | OpenAI integration for template generation (Responses API, models config, prompt management) |
| `analysis` | Segment analytics and event tracking |
| `applications` | Third-party integrations (Zapier) |
| `generics` | Shared mixins, base classes, permissions, filters, pagination |
| `storage` | File uploads/downloads, signed URLs (GCS, IBM COS) |

Each app typically has: `models/`, `serializers/`, `views/`, `services/`, `tasks/`, `permissions.py`, `filters.py`, `querysets.py`, `urls/`, `tests/`

## Commands

```bash
# Tests (from backend/)
pytest -vv .                          # Run all tests
pytest -vv src/processes/tests/       # Run specific app tests

# Linting (from repo root for pre-commit, or backend/ for direct)
ruff check --config backend/ruff.toml .
pycodestyle --config=backend/pycodestyle.ini .

# Django management (inside container or with proper env)
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py compilemessages
```

## Testing

- Framework: pytest + pytest-django
- Config: `pytest.ini` with `--dc=Testing` (uses Testing Django configuration)
- Testing config: in-memory caching, eager Celery (synchronous), no external services
- Each app has `tests/` directory with `conftest.py` fixtures
- Key fixtures: `api_client` (custom PneumaticApiClient), `mocker`, `identify_mock`

## Code Style

- **Ruff** (primary linter): `ruff.toml` — line length 79, single quotes, Python 3.7 target
- **Pycodestyle**: `pycodestyle.ini` — PEP 8 compliance
- **Pre-commit hooks**: ruff + pycodestyle run on commit
- Excludes: migrations, settings.py, messages.py, wsgi.py, asgi.py

## API Design

- REST API with DRF ViewSets & Routers (trailing_slash=False)
- Versioned endpoints: v1, v2, v3
- Auth: JWT (6h access / 7d refresh), custom Bearer tokens (Redis-cached), guest tokens
- Pagination: LimitOffsetPagination
- 13 configurable throttle rates (THROTTLE_01–THROTTLE_13)

## WebSocket Endpoints

- `/ws/notifications` — real-time notifications
- `/ws/workflows/new-task` — new task events
- `/ws/workflows/removed-task` — task removal events
- `/ws/workflows/events` — workflow state changes
- `/ws/events` — generic events

## Settings

`src/settings.py` uses django-configurations with 4 environment classes:
- `Common` — shared base config
- `Testing` — test overrides (in-memory cache, eager Celery)
- `Development` — local dev (Redis caching, Channels Redis)
- `Staging` / `Production` — database replicas, production settings

Environment selected via `ENVIRONMENT` env var. All config via env vars (see root `.env`).

## AI Template Generation

The AI service (`src/processes/services/templates/ai.py`) generates workflow templates from natural language:

- Uses OpenAI Responses API via direct HTTP calls (`requests` library, not the `openai` SDK)
- Default model: `gpt-4.1-mini`, default system prompt: `DEFAULT_TEMPLATE_INSTRUCTION`
- Both can be overridden via Django Admin (`/admin/ai/openaiprompt/`) by creating an active prompt with target "Get full template (JSON)"
- Available models defined in `src/ai/enums.py` (`OpenAiModel`)
- Templates include kickoff fields, task output fields with `api_name`, and variable references (`{{field-name}}`)
- Requires `OPENAI_API_KEY` env var; `OPENAI_API_ORG` is optional
