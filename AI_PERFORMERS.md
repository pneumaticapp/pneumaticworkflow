# AI Performers — branch `ai-performers`

Native AI task performers for Pneumatic: an AI agent can be assigned to a
workflow task exactly like a human performer; when the task starts, the agent
reads the task context (kickoff/output fields of prior steps, description,
attached documents), calls an LLM through an OpenAI-compatible provider
(OpenRouter by default), fills the task's output fields (including generating
Markdown documents into file fields), and completes the task so the workflow
chains onward. Humans and AI interleave freely across the steps of a template.

This document describes **what** is on this branch and **how** it works. It is
written for both Pneumatic developers and AI coding agents: paths are exact,
payload shapes are literal, and behavior contracts are stated as invariants.
The branch is ~36 commits on top of master `f61c176f`
(~10 000 insertions, 240+ files; backend ≈ new `src/ai` app + surgical
touches in `src/processes`, frontend ≈ one new page + performer plumbing).

---

## 1. Feature summary (user-visible)

- **AI Agents** — account-scoped, admin-managed entities (name, model slug,
  system prompt) with a management page at `/ai-agents/` and a CRUD API.
  Model slug is picked from a live, searchable catalog of models that support
  structured outputs (fetched from the provider).
- **Assign AI to template tasks** — the template editor's performer picker
  lists agents as `AI agent: {name}`. Humans and AI agents can share a task
  ("AI drafts, human approves" — see §7 for the completion semantics); a
  task with an AI performer must have at least one output field.
- **Automatic execution** — when a task with an AI performer starts, a Celery
  job runs the agent: field values from kickoff + earlier tasks are resolved,
  attachments in the task description are downloaded and fed to the model
  (text verbatim, images as vision blocks, PDF via pdfminer, DOCX via
  mammoth), the model is forced to return JSON matching a schema derived from
  the task's output fields, values are translated to Pneumatic's API
  conventions, generated documents are uploaded to the file service, and the
  task is completed *as the agent*.
- **Graceful degradation** — anything the agent can't handle safely (invalid
  output, unfetchable attachment, missing key…) leaves the task open for a
  human, with an explanatory event and a websocket notification.
- **Runtime add/remove** — AI performers can be added to / removed from a
  *running* task from the task card; adding dispatches a run immediately.
- **BYO provider key** — an account owner can save their own OpenRouter API
  key (`/ai/connection`); doing so activates the feature for the account and
  routes all its AI calls through that key.
- **Visibility** — timeline events for "agent completed" / "agent left the
  task", token usage metering per run, agents in the workflow highlights feed
  and the workflows performer filter, robot avatar in all performer renders,
  agent names in the Excel export.

## 2. Enablement / feature gates

Two-level gate, evaluated by `src/ai/providers.py::ai_performers_active(account)`:

```
active = settings.PROJECT_CONF['AI_PERFORMERS']        # env AI_PERFORMERS=yes
         AND (account.ai_performers_enabled            # operator-set flag
              OR account has an active AIProviderConnection)  # BYO key
```

- The deployment env flag is the master switch; without it nothing AI-related
  is reachable (permission class `AiPerformersEnabledPermission`).
- Saving a BYO key **self-enables** the feature for that account — no
  operator action needed. `/ai/connection` itself is gated on the env flag
  only (so an account can enable itself).
- Credential resolution (`resolve_provider(account)`): an active
  `AIProviderConnection` for the account wins; otherwise the platform-wide
  `settings.OPENROUTER_BASE_URL` / `OPENROUTER_API_KEY` (env, optional). With
  neither, a run fails cleanly (`AIClientError: missing api_key` →
  run FAILED, task stays open).

## 3. Data model (`backend/src/ai/models.py`, migration `0004`)

| Model | Purpose | Notes |
|---|---|---|
| `AIAgent` | account-scoped agent: `name`, `model_slug`, `system_prompt` | `SoftDeleteModel`; NOT a User row (deliberate — the repo removed an `is_robot` user type in its past) |
| `AIProviderConnection` | account's BYO provider credentials (base URL + key) | singleton-per-account in practice; key stored **plaintext** (prototype; encryption at rest is a known TODO); masked in API responses (`sk-or-v1••••cdef`) |
| `AITaskRun` | one execution attempt bundle per (agent, task) | statuses `queued → running → completed / left_for_human / failed` (`src/ai/enums.py::AITaskRunStatus`); records `prompt_tokens`, `completion_tokens`, served model, error detail |

Performer plumbing in `src/processes`:

- `PerformerType.AI = 'ai_agent'` (`src/processes/enums.py`).
- `ai_agent` FK added to `RawPerformerMixin` (template side,
  `models/mixins.py`) and `TaskPerformer` (runtime side,
  `models/workflows/task.py`) with a partial unique constraint on
  `(ai_agent, task)`.
- `Task.update_performers()` resolves template raw performers of type
  `ai_agent` into `TaskPerformer` rows; orphan cleanup handles AI rows;
  version sync no longer injects a default human performer into AI-only tasks
  (`services/tasks/task_version.py`).

Pre-existing models `OpenAiPrompt`/`OpenAiMessage` in the same app are the
repo's old, unrelated "generate template steps" feature — untouched, do not
extend them.

## 4. Execution pipeline

```
task starts (continue_task)                     template version sync            runtime add API
        │                                              │                                │
        └──────────────► src/ai/dispatch.py::dispatch_ai_performers ◄───────────────────┘
                          • gate: ai_performers_active(account)
                          • query active agents among task performers
                          • reset runs if task is_returned
                          • transaction.on_commit → run_ai_performer.delay   ← commit-safe (07d778a4)
                                        │
                          src/ai/tasks.py::run_ai_performer  (Celery)
                          • atomic claim QUEUED→RUNNING (idempotent under races)
                          • transient errors: retry ×5, then FAILED
                                        │
                          src/ai/services/performers.py::AIPerformerService
                          1. load()      — task/agent/run re-read; no-op if performer gone
                          2. resolve     — output fields of task → JSON schema
                                           (performers/output_fields.py, output_schema.py)
                          3. context     — field values via ORM, task description,
                                           attachments (performers/attachments.py)
                          4. _call_model — clients/chat_completions.py (requests, not httpx;
                                           py3.7-compatible), structured output enforced,
                                           creds from resolve_provider(account)
                          5. files       — performers/generated_files.py: {filename, content}
                                           answers for file fields → sanitize name → upload via
                                           FileServiceClient → value becomes ['[name](url)']
                          6. translate   — performers/output_translation.py → Pneumatic API
                                           value conventions (see §7)
                          7. complete    — complete_task_for_ai_agent → complete_task(ai_agent=…)
                                           (actor-neutral internals extracted in ed84cd26)
```

**Failure contract** (enforced in `AIPerformerService`):

- *Transient* (network/5xx/provider outage, file-service connection failure)
  → Celery retry up to 5×, then run `FAILED`, task stays open.
- *Semantic* (model output invalid against schema, attachment download 4xx,
  file upload rejected) → run `LEFT_FOR_HUMAN`: task stays open for humans,
  an `AI_AGENT_LEFT` timeline event records the reason, and a ws notification
  (`NotificationType.AI_LEFT_TASK`) goes to human co-performers, else the
  workflow starter, else the account owner.
- Configuration absent (no key anywhere) → `FAILED` with explicit message.
- All completions/timeline writes happen only on the happy path; a run never
  half-completes a task.

## 5. HTTP API surface (all under the backend root, gated as noted)

| Endpoint | Methods | Purpose |
|---|---|---|
| `/ai/agents` (+`/{id}`) | CRUD (DRF router) | agent management; admin-only writes, soft delete, duplicate-name 400. Gate: `AiPerformersEnabledPermission` |
| `/ai/connection` | GET/PUT/DELETE | BYO OpenRouter key singleton; admin/owner only; key live-verified on save (401/403 from provider → 400 `MSG_AI_0003`; provider outage → saved anyway); response masks the key. Gate: env flag only |
| `/ai/models` | GET | live model catalog filtered to `structured_outputs` support, cached 1 h per base_url; works keyless (catalog is public); failure → `[]` uncached |
| `/v2/tasks/{id}/create-ai-performer` | POST `{ai_agent_id}` | runtime add; validates feature active, agent account-owned+active, **task has output fields** (`MSG_PW_0095` — see §8), then dispatches immediately |
| `/v2/tasks/{id}/delete-ai-performer` | POST `{ai_agent_id}` | runtime remove (soft delete; queued run no-ops via `load()` check); last-performer guard; if the task then satisfies requires-all it auto-completes |
| Templates API | — | `raw_performers` accept `{type: 'ai_agent', source_id: '<agent id>', api_name}`; validation in `serializers/templates/raw_performer.py` (`MSG_PT_0075/0076`): flag on, id numeric, agent exists/owned/active; task-level rule (`MSG_PT_0078`, `serializers/templates/task.py`): a task with an AI performer must have output fields. Human+AI mixes and multiple agents per task are allowed |

Serialization notes: template API labels AI performers `AI agent: {name}`;
runtime `TaskUserGroupPerformerSerializer.get_source_id` returns the agent id
for `type='ai_agent'`; the version schema (`versioning/schemas.py`) carries
`ai_agent_id` (omitting it silently dropped AI performers on version sync).
Workflow list API accepts `current_performer_ai_agent_ids` for filtering.

## 6. Frontend map (`frontend/src/public`)

- **Redux slice `aiAgents`** — agent list, connection state, model catalog;
  `loadAiAgents` / `loadAiConnection` dispatched from the `MainLayout`
  bootstrap; a 403 from `/ai/agents` is swallowed and read as "feature off"
  (`isEnabled=false`), which also gates the menu item.
- **`/ai-agents/` page** — `views/AiAgents` + `components/AiAgents/*`:
  agent list, create/edit modal (model field is a searchable dropdown fed by
  `/ai/models`, falling back to free text when the catalog is empty), and the
  OpenRouter connection panel (save/remove key).
- **Template editor** — `getPerformersForDropdown` takes the agents list;
  `ETaskPerformerType.AiAgent = 'ai_agent'` (`types/template.ts`).
- **Runtime views** — robot avatar (`TUserType += 'ai_agent'`), task-card
  picker for runtime add/remove (hidden when the task has no output fields),
  `WorkflowLogAiAgent` timeline component for event types 24/25,
  notifications-panel case for `AI_LEFT_TASK`, highlights feed rendering,
  performer filter (`?ai_agents=` URL sync), Excel export shows agent names.
- **Testing gotchas** — `jest/jest.setup.js` holds a global redux mock state:
  *every new slice key must be added there* (`aiAgents` with `models` was).
  Several performer render maps are exhaustive mapped types — extending the
  enum forces entries (`TaskItemUsers`, both `PageTitle.tsx` maps,
  `FeedItemIcon`). `TaskCard.test` mocks selector *modules*, not state.

## 7. Behavior contracts worth knowing (live-verified)

These conventions were ported from a live-verified prototype and are enforced
by `output_translation.py` / relied on by the pipeline:

- **Task ordering is conditions, not numbers.** Tasks without conditions
  start in parallel. Sequential flow = a `start_task` condition whose
  predicate is `{field_type: 'task', operator: 'completed'|'completed_or_skipped',
  field: <task api_name>}`. `parents` is derived and read-only.
- **Choice fields (radio/dropdown) travel as display values**, not api_names
  — both in AI outputs and in condition predicates (`operator: 'equals'`,
  `field_type: 'radio'`, `value: 'Reject'`).
- **Dates are noon-UTC timestamps; strings cap at 140 chars** (text fields
  are unlimited); **file field values are lists of Markdown links**
  `["[name](public_url)"]` whose domain must match the file service
  (`FILE_SERVICE_PUBLIC_URL`).
- **Attachment intake** (`performers/attachments.py`): text-likes verbatim
  (80 KB cap), images become base64 vision content blocks, PDF via
  `pdfminer.six==20221105`, DOCX via `mammoth==1.6.0` (both pure-Python,
  last py3.7-compatible pins; empty PDF text is disclosed as "scanned
  document?"), legacy `.doc` disclosed as unsupported. Failures never crash a
  run: unsupported formats are *disclosed to the model* in the prompt.
- **Human+AI completion semantics** ("AI drafts, human approves"): an AI
  agent's completion **never closes a task that still has active human
  performers**, regardless of `require_completion_by_all` — the agent fills
  its output fields, its `TaskPerformer` is marked completed, an
  `AI_AGENT_COMPLETED` timeline event records the draft, and the task stays
  open for the humans. A human completing a non-requires-all task closes it
  immediately (as always), including over a still-pending agent (whose run
  then no-ops on the inactive task). An AI completion closes the task only
  when no active human performers remain: agent-only tasks, or requires-all
  tasks where every human already finished. The same rule lives in
  `Task.can_be_completed()` (used by the performer-removal paths), so
  removing the last human from a task whose agent already drafted completes
  it — credited via `Task.get_first_completed_human()` with the requesting
  admin as fallback. Tasks with no output fields refuse AI performers in
  both the template API (`MSG_PT_0078`) and the runtime add API
  (`MSG_PW_0095`): an agent there would instantly complete the task with an
  empty output.

## 8. Known gaps / TODOs (deliberate, in priority order)

1. **Phase 3 remainder** — AI agents as members of user groups, the
   `task_started` webhook + public agent API, per-agent connection override
   (`AIAgent.connection` FK exists but `resolve_provider` is account-level
   only), migrating the legacy template-generation feature onto the new
   provider layer. A ws/notification nudge to humans when an agent's draft
   lands ("AI completed its share") is a candidate UX addition — today the
   draft is visible via the timeline event and the filled fields.
2. **Phase 2 remainder** — provider-key **encryption at rest** (plaintext
   today, prototype-grade), billing hooks / per-account usage caps.
3. **`GET /navigation/menu` 404 on fresh DBs** (Railway) — no seeded menu
   rows; the UI falls back to its generated menu, cosmetic only.
4. **ru locale** — English placeholder strings exist in `ru_RU`; nothing
   breaks, translations skipped by request.
5. Pre-existing flake (master, not ours): reports
   `test_overview_query__date_range_filtering` boundary race — passes in
   isolation.

## 9. Infra & deployment notes

- **Env vars** (backend, celery, celery-beat): `AI_PERFORMERS=yes`,
  `OPENROUTER_API_KEY` (optional platform fallback; BYO keys make it
  unnecessary), `OPENROUTER_BASE_URL` (defaults to OpenRouter),
  `FILE_SERVICE_URL` (container-internal, e.g. `http://file-service:8000`),
  `FILE_SERVICE_PUBLIC_URL` (browser-facing, e.g. `https://host/files`) —
  the internal/public split (settings.py) is **required** for both docker
  compose networking and Railway private networking: uploads go direct,
  markdown-link validation checks the public domain.
- **nginx** (`nginx/railway/nginx.conf`): every top-level backend URL
  namespace must be present in the `@api` regex — `ai` was added
  (`2b8ec694`), and en route we found `fieldsets` missing on master too
  (`c6331e3e`). Symptom of a miss: the SPA's HTML is served to API calls.
- **Dependencies added**: `pdfminer.six==20221105`, `mammoth==1.6.0` only.
  The provider client uses `requests` (already a dependency) — no httpx, no
  OpenAI SDK; the backend is Python 3.7.5/Django 2.2 and the no-new-deps
  constraint was followed everywhere else.
- **Railway** — a full 13-service deployment of this branch runs at
  `nginx-proxy-production-072b.up.railway.app`. Template/deploy gotchas
  (file-service startCommand, IPv6 `::` binding, redis `sh -c` var expansion,
  redeploy-vs-fresh-deploy) are written up in
  `Railway_Deployment_Report.pdf` (kept outside the repo; ask the branch
  authors).

## 10. Testing & dev loop

- **Backend**: pytest with `--dc=Testing` (eager Celery, locmem caches — only
  Postgres needed). Full suite ≈ 5850 tests. AI app tests live in
  `src/ai/tests/` (~190). Test-naming convention
  `test_thing__condition__result` followed throughout. Note
  `src/ai/tests/conftest.py::immediate_on_commit` (autouse): Django 2.2 lacks
  `captureOnCommitCallbacks`, so `transaction.on_commit` in the dispatcher is
  patched to run inline.
- **Frontend**: jest ≈ 1550 tests green; one *environment* failure exists on
  node 24 (`src/server/utils/__tests__/request.test.ts` crashes the worker
  with 0 test failures — repo targets node 18).
- **Lint**: ruff per repo `ruff.toml` (79 cols, single quotes, trailing
  commas); tsc + eslint clean for branch files.
- **Migration caution**: the repo has pre-existing model/migration drift —
  `makemigrations` emits unrelated destructive operations. Both migrations on
  this branch (`ai/0004`, `processes/0256`) were hand-pruned to their own
  ops; do the same for any follow-up.

## 11. Commit index (bottom-up)

Phase 0 — foundations: `4cb527ab` provider client + output schema/translation
ports (pure logic, 49 tests) · `ed84cd26` actor-neutral task-completion
internals extracted from `complete_task_for_user`.

Phase 1 — MVP: `a166a448` data model · `a02338d8` execution pipeline +
dispatch · `a5409028` template→task performer resolution · `801cfed9`
template validation + `/ai/agents` CRUD · `2aff56cc`+`800cf5c6` performer
picker · `e7240592` AI Agents page · `4e86b0f0`+`bc657b54` runtime display ·
`1ba21941` dispatch on template version sync · `920dd398`+`b5c2dcab`+
`111f3085` events, notifications, token metering, env plumbing · `fb880315`
attachments in prompts · `11a21551` generated documents (file outputs) ·
`73288b9b` PDF/DOCX extraction · `1ab7ef2a` file-service internal/public URL
split · `4681ac32`+`e9d62bd7` highlights, filters, requires-all events.

Phase 2 (partial): `7ac93c32`+`d326bbda` BYO OpenRouter keys ·
`7976f461`+`c5b4a87e` live model catalog · `0833b131` AI-agents page layout.

Phase 3: `3c3599be`+`df8f1175` runtime add/remove AI performers ·
`7231ae2a` runtime no-output-fields guard · `7251c31b` template-side
no-output-fields guard · `a7a88e4e` human+AI co-assignees ("AI drafts,
human approves" completion semantics, sole-performer rule removed).

Infra/fixes: `2b8ec694` `/ai` nginx routing · `c6331e3e` `/fieldsets` nginx
routing (pre-existing master bug) · `07d778a4` dispatch-after-commit race fix
· `7d7da56e` UI font → Roboto (unrelated restyle, kept).
