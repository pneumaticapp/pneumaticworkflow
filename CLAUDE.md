# Pneumatic Workflow

Open-source SaaS workflow management platform. Monorepo with Django backend, React frontend, and Docker-based infrastructure.

## Architecture

- **Backend**: Django 2.2 + DRF 3.13.1, Python 3.7.5+, PostgreSQL 15, Redis 6.2.6, Celery 4.4.7, RabbitMQ 3.13, Django Channels (WebSockets)
- **Frontend**: React 17 + TypeScript 5.3, Redux + Redux Saga, Express server (SSR/proxy), Webpack
- **Infrastructure**: Docker Compose (8 containers), Nginx reverse proxy, GitHub Actions CI/CD

## Running Locally

```bash
./start.sh [address]        # First-time setup: generates .env, starts containers
docker compose up -d        # Start all services
docker compose down         # Stop all services
```

- Frontend: `http://localhost`
- Backend admin: `http://localhost:8001/admin`
- Forms: `http://form.localhost`
- RabbitMQ management: `http://localhost:15672`

## Key Services (Docker)

| Service | Container | Port |
|---------|-----------|------|
| PostgreSQL 15 | pneumatic-postgres | 5432 |
| Redis 6.2.6 | pneumatic-redis | 6379 |
| RabbitMQ 3.13 | pneumatic-rabbitmq | 5672 |
| Django/Gunicorn | pneumatic-backend | Unix socket |
| Celery Worker | pneumatic-celery | - |
| Celery Beat | pneumatic-celery-beat | - |
| Node.js/React | pneumatic-frontend | 8000 |
| Nginx 1.25.4 | pneumatic-nginx | 80, 443, 8001 |

## AI Template Generation

- Uses the OpenAI Responses API (direct HTTP calls, not the openai SDK)
- Default model: `gpt-4.1-mini` (configurable via Django Admin)
- System prompt and model can be overridden at `http://localhost:8001/admin/ai/openaiprompt/`
- Requires `AI=yes` and `OPENAI_API_KEY` in `.env` (`OPENAI_API_ORG` is optional)
- See `AI_GENERATION.md` for full configuration docs, `SYSTEM_PROMPT.md` for the default prompt

## Environment

All configuration via `.env` file at project root. Feature toggles are `yes/no` flags:
`BILLING`, `EMAIL`, `AI`, `PUSH`, `STORAGE`, `ANALYTICS`, `CAPTCHA`, `SIGNUP`, `MS_AUTH`, `GOOGLE_AUTH`, `SSO_AUTH`

## CI/CD

GitHub Actions workflows in `.github/workflows/`:
- `backend-latest-push.yml` — builds backend/celery/celery-beat images on master push
- `frontend-latest-push.yml` — builds frontend image on master push
- `new-tag-push.yml` — builds all images on `v*` tags with `:stable` tag
- All images pushed to Docker Hub: `pneumaticworkflow/*`
- Multi-platform: linux/amd64, linux/arm64

## Scripts

- `scripts/create_backup.sh` — PostgreSQL backup dump
- `scripts/install_updates.sh` — pull latest code, rebuild containers
