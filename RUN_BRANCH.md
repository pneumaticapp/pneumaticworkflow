# Running this branch

This branch adds enhanced AI template generation to Pneumatic, including:

- OpenAI Responses API (replacing the legacy Chat Completions API)
- Updated model list (gpt-4.1-mini, gpt-4.1, gpt-5, o3, o4-mini, etc.)
- Template generation with workflow variables (kickoff fields and output fields with api_name support)
- Multi-line prompt input in the template generator UI

## Prerequisites

- Docker and Docker Compose installed
- An OpenAI API key (https://platform.openai.com/api-keys)

## Setup

### 1. Clone and checkout the branch

```bash
git clone git@github.com:pneumaticapp/pneumaticworkflow.git
cd pneumaticworkflow
git checkout backend/ai/upgrade_openai_responses_api_and_template_generation
```

### 2. Create the `.env` file

Create a `.env` file in the project root with the following content:

```env
# Pneumatic Workflow Configuration
AI=yes
OPENAI_API_KEY=sk-your-openai-api-key-here

# URLs (localhost setup)
BACKEND_URL=http://localhost:8001
FRONTEND_URL=http://localhost
FORMS_URL=http://form.localhost
FRONTEND_DOMAIN=localhost
BACKEND_DOMAIN=localhost
FORM_DOMAIN=form.localhost
WSS_URL=ws://localhost:8001

# Service passwords (change these for production)
POSTGRES_PASSWORD=change-me-postgres
POSTGRES_REPLICA_PASSWORD=change-me-postgres
REDIS_PASSWORD=change-me-redis
RABBITMQ_PASSWORD=change-me-rabbitmq
```

Replace `sk-your-openai-api-key-here` with your actual OpenAI API key.

### 3. Build the frontend image

The frontend changes (multi-line prompt input) require building the image locally:

```bash
docker compose build frontend
```

This takes several minutes (npm install + webpack build).

### 4. Start the application

```bash
docker compose up -d
```

### 5. Run database migrations

Once the backend container is healthy:

```bash
docker exec pneumatic-backend python manage.py migrate
```

### 6. Access the application

- **Frontend**: http://localhost
- **Backend admin**: http://localhost:8001/admin
- **RabbitMQ management**: http://localhost:15672

The frontend takes a few minutes to become available on first start (webpack production build runs inside the container). You can monitor progress with:

```bash
docker compose logs -f frontend
```

## Using AI template generation

1. Log in to the application
2. Create a new template
3. Click the AI generate button
4. Enter a description of your business process in the multi-line text area
5. Click Generate

The default model is `gpt-4.1-mini`. You can change the model and customize the system prompt via the Django admin panel at http://localhost:8001/admin/ai/openaiprompt/.

## Stopping the application

```bash
docker compose down
```
