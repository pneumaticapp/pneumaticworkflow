# Changes in this branch

## Backend

### OpenAI API migration: Chat Completions → Responses API

**File**: `backend/src/processes/services/templates/ai.py`

- Replaced the legacy `openai.ChatCompletion.create()` calls (openai SDK v0.27) with direct HTTP calls to the OpenAI Responses API (`https://api.openai.com/v1/responses`)
- The Responses API uses `instructions` (system prompt) + `input` (user message) instead of a `messages` array
- Used the `requests` library (already a dependency) for HTTP calls instead of upgrading the `openai` package, which would require Python 3.8+ (the container runs Python 3.7)
- Removed the `import openai` dependency from the service module entirely
- Updated error handling: replaced `openai.error.OpenAIError` references with generic `Exception` handling and simplified Sentry logging payloads
- Added `_call_responses_api()` method to `BaseAiService` that handles the HTTP call and response parsing
- Added `_openai_headers()` helper for auth header construction
- Removed the requirement for `OPENAI_API_ORG` — only `OPENAI_API_KEY` is now needed (org is optional)

### Updated model list

**File**: `backend/src/ai/enums.py`

Added new models to `OpenAiModel`:
- `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`
- `gpt-5`, `gpt-5-mini`
- `o3`, `o4-mini`

The dropdown in Django Admin now shows these models with `gpt-4.1-mini` listed first as recommended. All legacy models (gpt-3.5-turbo, gpt-4, gpt-4o, etc.) are still available.

**Migration**: `backend/src/ai/migrations/0005_update_model_choices.py`

### Default model changed

**File**: `backend/src/processes/services/templates/ai.py`

- Changed from `gpt-4o` to `gpt-4.1-mini` as the default model when no prompt is configured in Django Admin

### Enhanced system prompt for template generation

**File**: `backend/src/processes/services/templates/ai.py`

The `DEFAULT_TEMPLATE_INSTRUCTION` was rewritten to produce richer templates:
- Fields now include `api_name` (e.g., `field-project-name`) that the AI specifies directly
- Task descriptions can reference kickoff and previous task field values using `{{field-project-name}}` syntax
- The `_normalize_field()` method now preserves the AI-provided `api_name` instead of always generating a random one, so variable references in task descriptions actually resolve correctly

### Test response updated

**File**: `backend/src/processes/services/templates/ai.py`

- The `_test_response()` (honey harvesting template used when no API key is set) now includes `api_name` on all fields to match the new format

### Tests updated

**File**: `backend/src/processes/tests/test_services/test_templates/test_ai/test_open_ai_service.py`

- Rewrote tests to mock `_call_responses_api` instead of `openai.ChatCompletion.create`
- Removed `import openai.error` dependency
- Added tests for the Responses API integration

## Frontend

### Multi-line prompt input

**Files**:
- `frontend/src/public/components/TemplateAIModal/TemplateAIModal.tsx`
- `frontend/src/public/components/TemplateAIModal/TemplateAIModal.css`

- Replaced the single-line `<InputField>` with a `<textarea>` (4 rows, resizable)
- Enter key now inserts a newline instead of submitting the form (click the button to generate)
- Button moved below the textarea at its natural width instead of stretching to match the input
- Updated `inputRef` type from `HTMLInputElement` to `HTMLTextAreaElement`
- Removed unused `InputField` import

## Infrastructure

### Docker Compose

**File**: `docker-compose.yml`

No permanent changes. The frontend still uses the pre-built Docker image (no volume mount).

### .gitignore

**File**: `.gitignore`

Added CLAUDE.md files.

## Impact on running the branch

Because the frontend changes are in source code but the `docker-compose.yml` pulls a pre-built image from Docker Hub, anyone running this branch must **build the frontend image locally** before starting the containers:

```bash
docker compose build frontend
docker compose up -d
docker exec pneumatic-backend python manage.py migrate
```

The backend changes are picked up automatically since `./backend` is volume-mounted into the container.

See `RUN_BRANCH.md` for full setup instructions and `AI_GENERATION.md` for AI configuration details.
