# AI Template Generation

Pneumatic can generate workflow templates from natural language descriptions using OpenAI. This document explains how it works and how to customize it.

## How it works

1. A user enters a business process description in the template editor
2. The backend sends the description to the OpenAI Responses API along with a system prompt (instructions)
3. OpenAI returns a JSON template with tasks, kickoff fields, and output fields
4. The template is parsed and loaded into the editor for the user to review and adjust

## Requirements

In your `.env` file:

```env
AI=yes
OPENAI_API_KEY=sk-your-key-here
```

`OPENAI_API_ORG` is optional. If omitted, OpenAI will use the default organization for your API key.

## Defaults (no configuration needed)

Out of the box, the system uses:

- **Model**: `gpt-4.1-mini`
- **System prompt**: A hardcoded instruction that tells the AI to generate workflow template JSON with kickoff fields, task output fields, and variable references

The default system prompt is defined in `backend/src/processes/services/templates/ai.py` as `DEFAULT_TEMPLATE_INSTRUCTION`. It instructs the AI to:

- Return valid JSON matching the Pneumatic template structure
- Include kickoff fields (information needed to start the workflow)
- Include task output fields (information produced during each task)
- Use `api_name` identifiers on fields (e.g., `field-project-name`)
- Reference field values in task descriptions using `{{field-project-name}}` syntax
- Support field types: string, text, radio, checkbox, date, url, dropdown, file, user, number

These defaults are used when no custom prompt is configured in Django Admin.

## Customizing via Django Admin

You can override the default model and system prompt by creating a prompt configuration in the Django Admin panel.

### Step 1: Access the admin panel

Go to http://localhost:8001/admin/ai/openaiprompt/ and log in.

### Step 2: Create a new prompt

Click "Add OpenAI Prompt" and configure:

| Field | Description |
|-------|-------------|
| **Is active** | Must be checked. Only one active prompt per target is allowed |
| **Target** | Select **"Get full template (JSON)"** |
| **Model** | Choose from the dropdown (see available models below) |
| **Temperature** | Controls randomness (0 = deterministic, 2 = creative). Default: 1 |
| **Top p** | Nucleus sampling (0-2). Alternative to temperature. Default: 1 |
| **Presence penalty** | Encourages new topics (-2 to 2). Default: 0 |
| **Frequency penalty** | Discourages repetition (-2 to 2). Default: 0 |

### Step 3: Add messages

Add messages (inline at the bottom of the form) to define the conversation sent to OpenAI:

| Order | Role | Content |
|-------|------|---------|
| 1 | **system** | Your custom system prompt (instructions for the AI) |
| 2 | **user** | `{{ user_description }}` |

The `{{ user_description }}` placeholder is replaced with the actual text the user enters in the template generator.

**Example system message:**

```
You are a workflow template designer for a marketing agency.
Generate templates with detailed task descriptions and relevant fields.
Always include a review/approval step.
Return ONLY valid JSON matching the Pneumatic template structure.
```

### Priority

- If an **active** prompt with target "Get full template (JSON)" exists in the database, its messages and model are used
- If no such prompt exists, the hardcoded `DEFAULT_TEMPLATE_INSTRUCTION` and `gpt-4.1-mini` are used

## Available models

| Model | Best for |
|-------|----------|
| **gpt-4.1-mini** (recommended) | Best balance of quality, speed, and cost for structured JSON generation |
| gpt-4.1 | Higher quality, slower, more expensive |
| gpt-4.1-nano | Cheapest and fastest, good for simple templates |
| gpt-5 | Latest flagship model |
| gpt-5-mini | Latest smaller model |
| o3 | Advanced reasoning (for complex multi-step processes) |
| o4-mini | Fast reasoning model |
| gpt-4o | Previous generation, still capable |
| gpt-4o-mini | Previous generation, smaller |

## Template variables

The AI generates fields with `api_name` identifiers that can be referenced in task descriptions:

- A kickoff field with `api_name: "field-project-name"` can be referenced in any task description as `{{field-project-name}}`
- A task output field can be referenced in subsequent task descriptions using the same syntax
- This allows data to flow through the workflow from kickoff to completion

## Architecture

The AI service code lives in:

- `backend/src/processes/services/templates/ai.py` — Main service (API calls, JSON parsing, template construction)
- `backend/src/ai/models.py` — Django models for prompt configuration
- `backend/src/ai/enums.py` — Available models and prompt targets
- `frontend/src/public/components/TemplateAIModal/` — Frontend UI component
