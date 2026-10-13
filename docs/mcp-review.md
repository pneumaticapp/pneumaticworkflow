# MCP standards review — 2026-10-09

## Changes outside MCP rolled back — 2026-10-13

At the user's request, unrelated refactoring was rolled back in stages:

1. Original Stripe services and eager initialization were restored. The extra
   transport, explicit `synchronize()` calls and constructor tests were removed.
2. Formatting-only changes in existing backend code and tests were restored.
3. SettingsLayout again uses its original class, container, selectors and CSS;
   its only production additions are the MCP connection-link import and element.
4. Template persistence again lives in the original TemplateSerializer;
   TemplateWriteService and its separate tests were removed.
5. The original flat `processes/queries.py`, attachment queryset location and
   attachment service/list SQL were restored. The MCP file filters and batch
   access checks remain, without AttachmentPermissionService or a query adapter.
6. Original webhook delivery/retry behavior was restored. The unrelated accounts
   0147 and processes 0261 migration additions were removed from source and index.

Together with the previous notification and starter-policy rollbacks,
`workflow_action.py` now matches Git HEAD completely, including its imports.
CommitTask, WorkflowNotificationService, TaskStarterService and StarterTaskResult
remain removed. The historical checkpoints below describe superseded states.
OAuth, MCP scopes, file isolation, upload lifecycle, secret redaction and MCP
frontend routes remain in place. No replacement abstractions were introduced.

Fresh local validation: **7,381 backend/public MCP catalogue cases passed**
across four PostgreSQL-backed shards (1,734 + 1,851 + 2,046 + 1,750), with zero
failures, errors or skips. The real local OAuth/core/MCP HTTP lifecycle passed
separately (one case). Stage-specific regressions passed: Stripe 789, templates
1,266, storage/queries/MCP files 598 and webhooks 59. After the final formatting
cleanup and removal of an unrelated assertion change, the original fieldset
suite passed all 86 cases. Frontend SettingsLayout/MCP/routes/login passed
**61 tests in four suites**. Optional live storage-provider byte delivery was
not exercised.

Ruff, whitespace and Django system checks passed. All 1,711 Python files parsed;
the final test-container manifest matches all 1,826 workspace source files.
The restoration audit verifies 49 original files against Git HEAD. TypeScript
passes with `--skipLibCheck`; the unrestricted check still reports existing
dependency declaration conflicts in node_modules. MCP/authentication/storage
migration checks pass. Accounts/processes still have their pre-existing model
state drift (ApiKey ordering, Account.max_users and WorkflowEvent.type); fixing
that drift would reintroduce the unrelated migrations and was excluded.

Before-file snapshots, restoration audit, manifests, logs and JUnit reports are
retained in `.mcp-validation/mcp-scope-rollback-20261013`. Only the three temporary
containers created for this validation were removed. No commit, push or
deployment was made.

## Workflow action restored to minimal diff — 2026-10-13

`workflow_action.py` matches the original Git HEAD byte for byte except one
import: `GetTaskPerformersQuery` now comes from `processes.queries.tasks`.
The original formatting, inline field query and starter completion/skip methods
are restored. Vacation delegation again uses the original boolean
`skip_delegated_task_for_starter`; its production file matches HEAD. The unused
starter service, result enum and dedicated rule tests were removed. The starter
service/result-enum descriptions in earlier checkpoints below are superseded.

Fresh validation: **297 tests passed**, with no failures, errors or skips,
covering workflow actions, vacation delegation, its Celery task and RCBA bug
regressions. Ruff, whitespace and Django checks passed. Reports and before-file
snapshots are retained in `.mcp-validation/workflow-minimal-20261013`.

## Notification structure restored — 2026-10-13

Following the user's review, the extra notification abstractions were removed.
`CommitTask` no longer exists. `NotificationTask` and `WebhookTask` again inherit
the original `celery.Task` classes, with normal `.delay()` scheduling throughout
their callers. The argument-copying and after-commit APIs and their dedicated
tests were removed; existing independent `transaction.on_commit` hooks remain.
Webhook timeouts and correct network-error logging/retry handling are retained.

`WorkflowNotificationService` was removed. Its only caller, `continue_task`,
again contains the original recipient selection and email/push/websocket payload
construction inline. No replacement helper or service was introduced.

Fresh local validation after this rollback: **2,016 regression cases passed**
across notifications, webhooks, workflow/task actions and views, performer and
version services, groups, vacations and reports. The real local OAuth/core/MCP
HTTP lifecycle also passed separately (one case). Both runs had zero failures,
errors or skips; optional live storage-byte provider integration was not enabled.
Ruff, whitespace and Django system checks passed. The restored inline block
matches the original Git block exactly, and the test container source matches
the final workspace manifest. Logs and JUnit evidence are retained in
`.mcp-validation/notification-rollback-20261013`. The three temporary containers
were removed after saving the reports. No commit, push or deployment was made.

The checkpoints below describe earlier states, including their test results.
Their notification abstraction/after-commit descriptions are superseded by this
section; the other domain refactors remain in place.

## Six backend domain refactors — 2026-10-13

The follow-up review recommendations were implemented in their agreed order:

1. `CommitTask` is the shared Celery base for notifications and workflow
   webhooks. Both `delay_on_commit` and `apply_async_on_commit` freeze arguments
   and scheduling options. Workflow webhooks now wait for the outer commit.
   Delivery uses a bounded connection/read timeout; real requests connection
   and timeout failures are logged as FAILED and participate in task retries.
2. `AttachmentPermissionService` owns grants, rebuilds and single/batch checks.
   `AttachmentQuerySet` belongs to storage; `accessible_to` is the common access
   selector, also used by the paginated list/count adapter. Existing list grant
   scope is preserved explicitly: it includes legacy personal/deleted group
   memberships, whereas private single/batch access uses live non-personal
   groups and account restrictions. The unused single account-file check is
   removed. Batch checks retain two queries with a warmed ContentType cache.
3. `TemplateWriteService` owns publishing, tree synchronization, draft saves,
   version snapshots, integration creation and discard. Tree and draft/version
   writes share a transaction. `TemplateSerializer` keeps input validation and
   response encoding; the service accepts a narrow encoding callback and domain
   context, without retaining the parent serializer or HTTP request. Existing
   nested serializers remain the child validation/write adapters.
4. `TaskStarterService` receives only starter/external-workflow facts and returns
   decisions. It no longer holds `WorkflowActionService` or calls its private
   methods. Performer writes, delay cleanup, events and graph transitions remain
   in the workflow command. Delegation checks task completion after applying the
   starter effect, preserving RCBA transitions and explicit `StarterTaskResult`.
5. The former `processes/queries.py` is split into `workflows`, `tasks`,
   `templates`, `dashboard` and `common`. Callers import their owning module.
   All 19 class AST bodies, including SQL and parameter construction, match the
   task-start snapshot; there is no compatibility re-export layer.
6. `StripeTransport` owns SDK calls, including object saves and invoice actions.
   `StripeService` construction no longer loads provider state or changes a
   local subscription. All product callers explicitly invoke `synchronize()`.
   The existing synchronization order, billing reconciliation and purchase
   behavior remain covered; provider state can be injected through the transport.

Model class bodies and migration files match the task-start snapshot. Moving
OAuth/upload model identities or changing the database schema remains a separate
stage. Existing MCP/frontend feature work is retained. No commit, push,
deployment, charge or production change is part of this refactor.

Final local validation: four disjoint PostgreSQL-backed shards passed
**1,830 + 1,786 + 2,013 + 1,779 = 7,408 tests**, with zero failures, errors or
skips, including the public MCP catalogue contract. The real local OAuth/core/
MCP HTTP lifecycle passed separately (one case); optional live storage-byte
provider integration was not enabled, and Stripe tests use provider mocks.
The full final run covers the corrected synchronization mocks and the added
commit/rollback, starter-policy and constructor-side-effect regressions.

Ruff, whitespace checks, Django system checks and migration drift checks for
accounts/authentication/processes/storage/MCP passed. All 1,711 Python source
files in the test container matched the final workspace manifest, with no extra
Python files. Ten moved attachment grant/rebuild methods also match their
original AST bodies. Logs, JUnit reports, before/final manifests and the delta
are retained in the ignored `.mcp-validation/domain-refactor-20261013` directory.
Earlier focused failures in that directory record corrected test-fixture/mock
expectations; the final full-suite reports are all green. The three disposable
containers for this run were removed after preserving evidence.

## Backend service boundaries and notification commit — 2026-10-13

UploadTargetService now belongs to storage.services.upload_targets. Upload and
credential services no longer import the MCP target adapter. UploadFieldService
owns process field selection and nested fieldset traversal; McpPayloadService
keeps scope enforcement, protocol references and upload-reference conversion.
Upload consumption and the workflow write retain their surrounding transaction.

AttachmentService.check_account_files_permission checks a batch with correlated
permission EXISTS queries. It preserves current-account record ownership,
any-live-attachment access, PUBLIC access and user/group grants. The regression
test verifies two SQL queries for 50 files with a warmed ContentType cache.
Deleted references and foreign private/account files cannot grant access.

Upload import, dispatch and cleanup tasks live in storage.tasks. Their explicit
registered src.mcp.tasks names, beat schedules, routes and feature gates are
unchanged. The combined credential/upload pruning task remains in MCP.

OAuth views and responses own JSON parsing, metadata validation and public
registration response conversion. ClientRegistrationService receives a client
identifier and persists policy; TokenExchangeService accepts a plain mapping.
Neither service accepts HTTP requests or responses.

TaskStarterService owns starter completion/skip rules. The workflow command
returns an explicit StarterTaskResult: unchanged, performers completed, task
completed or task skipped. Vacation delegation collects only fully skipped task
IDs. WorkflowNotificationService owns task-start recipients and payloads.

NotificationTask uses DjangoTask.delay_on_commit and snapshots its arguments.
Workflow actions, task/group/performer updates and the dynamic account-group
notification dispatcher publish workflow notifications only after commit.
Rollback and nested-savepoint regression tests verify that cancelled actions
publish nothing. Normal Celery scheduling remains; no notification outbox or
generic write-replay ledger was introduced.

Validation used four disjoint PostgreSQL-backed shards: 1,816 + 1,895 + 1,905 +
1,769 = **7,385 passed**, zero failures, errors or skips, including the public
MCP catalogue contract. The initial complete collection exposed ten group
notification regressions; after fixing the dynamic dispatcher, 90 focused
group/delegation cases and the entire 1,769-case shard passed. Other successful
shards were retained. The first contract collection attempts lacked the SDK in
the older test image; the successful shard used the existing matching SDK image.

The final real OAuth/core/MCP HTTP lifecycle passed (one case). This run did not
enable the optional live storage-byte provider. Ruff, whitespace, Django system
checks and migration drift checks for accounts/authentication/processes/storage/
MCP passed. Models and migrations are byte-identical to the task-start snapshot.
Logs and JUnit evidence are retained in the ignored
.mcp-validation/backend-blocks-20261013 directory. Existing uncommitted feature
work is preserved. No commit, push, deployment or production change was made.

## Remaining domain ownership and retention — 2026-10-13

UploadFieldService in processes owns task/kickoff field resolution. The MCP
UploadTargetService only validates the live connection and exact session
binding. McpPayloadService validates protocol references and scopes, then calls
UploadSessionService.consume for a locked, transactional READY-to-ATTACHED
transition. Workflow run/task completion keep their surrounding transaction,
so a later business validation failure restores the ready upload.

Upload/import enums, limits and exceptions belong to storage; InactiveGrant and
authentication messages belong to authentication. The translated texts, error
codes and response shapes are preserved. ExpiringQuerySet is a plain shared
QuerySet in generics, without introducing soft-delete semantics.

Import URL syntax validation lives in storage.validators. Malformed IPv6 URLs
and invalid ports now produce the standard validation response (400), instead
of an uncaught ValueError. File-service DNS/IP validation remains at the actual
download boundary.

CredentialPruneService removes bounded batches of expired credentials.
UploadPruneService clears finished source URLs and removes finished import jobs
and attached sessions 30 days after their expiry, at most 500 of each per pass.
Locked rows are skipped. A session is removed only after its import job is gone;
active jobs and file attachments are preserved. Unattached sessions, including
CLEANED, retain the fence required by storage deletion retries: CLEANED is an
authorization to delete, not proof that external deletion succeeded.
Celery task names, routes, model identities and the single initial migration
remain unchanged.

Local validation: all 7,373 backend/public-tool-contract cases passed across
four isolated PostgreSQL databases, including rollback, retention, file
preservation and locked-job/session pruning. The real OAuth/core/MCP HTTP
lifecycle and all ten storage filename-contract cases passed. Ruff, whitespace,
Django system checks and migration drift checks for the affected apps passed.
No commit, push, deployment or production data cleanup was performed.

## Upload lifecycle and service ownership — 2026-10-13

UploadSessionService and ImportService now live in backend storage.services.
Session creation and capability issuance share one transaction. Import claims
lock the connection before the session, matching completion callbacks. Failure
updates only pending/importing sessions; ready/attached files remain usable,
including when a caller holds an outdated session object.

FileAccessService now lives in authentication and handles credentials, scopes
and source-token validity. Completion and cleanup live in UploadSessionService;
account-bound attachment retrieval and file permission checks use the existing
AttachmentService. Public-file access in ordinary endpoints is preserved.
Connection lifecycle, connection views/serializers, OAuth enums and credential
constants also live in authentication. File patterns, timeout and the internal
storage-response error belong to storage. There are no compatibility reexports.

Upload and payload services take explicit user, delegation and data arguments,
without HTTP Request. TaskFieldQuerySet.for_task and
FieldTemplateQuerySet.for_kickoff share parent/fieldset selection; each caller
keeps its own permission, visibility and deletion filters. MCP keeps protocol
adapters, operation allowlists and model bindings. Models and the single initial
MCP migration are unchanged.

Local validation covered all 7,356 backend/public-tool-contract cases across
four isolated PostgreSQL databases. Two admin tests initially lacked a static
manifest in the new container; both passed after collectstatic, without source
changes. Seven focused upload/concurrency cases passed (overlapping the full
suite), as did the real OAuth/core/MCP HTTP lifecycle and all ten storage
filename-contract cases. Ruff, whitespace, Django system checks and migration
drift checks for MCP/authentication/accounts/processes/storage passed.
No commit, push, deployment or production database change was performed.

## Shared backend ownership — 2026-10-13

MCP and ordinary REST permissions now share template-access and task-performer
queries in processes.permissions; the REST guest-task restriction is preserved.
Billing composition and non-HTTP billing checks live in accounts.permissions.
BaseInputSerializer lives in generics.serializers. Opaque credential helpers
and protocol authentication exceptions live in authentication; existing
PneumaticToken formats and validation remain unchanged.

Pure filename, MIME and file-ID helpers live in backend storage.file_metadata,
with shared storage constants/messages. The existing FileServiceClient owns
both user uploads and post_internal for MCP storage calls. The latter preserves
its private URL, service secret, timeout, proxy and redirect restrictions.
The unused replay target check is removed. MCP retains its operation/scope
allowlist and model/consent bindings; upload/import behavior now lives in storage
and credential behavior in authentication as described above.
Models and migration history are unchanged.

Local validation: all 7,352 collected backend/public-tool-contract cases passed
across four isolated PostgreSQL databases. The real OAuth/core/MCP HTTP lifecycle
passed, and all 10 storage filename-contract cases passed. Cold-start/throttle/
redaction checks passed (13 cases, overlapping the full suite). Ruff, whitespace
and Django system checks passed. Migration drift checks passed for accounts,
authentication, processes, storage and MCP. The repository-wide check still
reports unchanged logs/permissions model-history drift; no migrations or models
were changed in this consolidation. No commit, push or deployment was performed.


## Execution layer removal — 2026-10-13

McpExecutionMiddleware, the generic MCP idempotency ledger and notification
outbox have been removed. Core writes use the ordinary backend behavior and
Celery tasks. Write tool schemas no longer require idempotency_key, and their
idempotentHint is false. OAuth authentication, live permissions, upload sessions
and durable URL import jobs remain. The single initial migration mcp.0001_initial creates only the current MCP
models; execution tables and the obsolete outbox schedule are not created.

Final local checks: 555 backend/MCP write regressions passed; 338 MCP resource
server tests passed; the real core/OAuth/SDK HTTP lifecycle passed. Django system
checks, migration drift checks, Ruff and whitespace checks passed. An isolated
migration readback verified removal of both execution tables, obsolete beat
schedule and refresh of the beat change timestamp, with uploads/imports retained.
No production migration, commit, push or deployment was performed.

The dated results and implementation descriptions below are historical
snapshots; their replay and notification-outbox claims no longer describe the
current implementation.

Scope: the uncommitted MCP feature, including Django, the separate MCP and file
services, frontend consent/upload flows, routing, CI and regression tests.
The existing worktree was preserved. No commit, push or deployment is part of
this review.

Review sources:

- `D:/Dev/knowledge/.agent/workflows/backend-revue.md`
- `D:/Dev/knowledge/.agent/workflows/backend-tests.md`

## Logical refactoring 2026-10-12

This refactoring preserves the existing uncommitted feature and the subsequent
MCP middleware cleanup. It changes module ownership and orchestration without
changing the public tool schemas, database schema or migration history.

- Django `views/` and `serializers/` now contain `base`, `oauth`, `consent`,
  `connections`, `delegation`, `files`, `uploads` and `templates` modules.
  Their `__init__.py` files are empty; routes, services and tests import the
  owning module directly. All 28 view classes and 30 serializer classes have
  the same AST as before the move. Shared upload responses remain in
  `serializers/uploads.py`, including those used by file acknowledgement.
- Idempotency and replay authorization live in `services/idempotency.py`.
  Their transaction, permission and replay rules are unchanged.
  `ImportService` calls `StorageClient` directly; it no longer imports the
  Celery task module through the `storage_post` pass-through wrapper.
- The MCP service separates input validation (`tool_inputs.py`), the public
  catalogue (`tool_catalog.py`), output models (`outputs.py`), response
  conversion/size limits (`normalization.py`) and execution (`tools.py`).
  Each tool declares its scopes and output model in the catalogue. The core
  retains its independent operation allowlist. `call_tool` now orchestrates
  validation, scope policy, dispatch, attachment enrichment and error mapping
  in 60 lines, down from 208. The existing `app.py` middleware separation is
  preserved; only the catalogue import changed.
- Storage's `MCPImportService` owns fetch/store/reconciliation, while
  `MCPDownloadService` owns ticket persistence, expiry and live authorization.
  FastAPI dependencies supply their infrastructure. File request identity
  stays in the HTTP layer. Import and download handlers are each 24 lines;
  byte limits, post-fetch grant validation, upload recovery, ticket hashes,
  expiry and Range/revocation checks are preserved. Filename sanitization
  is shared in `shared_kernel/security/filename.py`.
- `test_mcp_tool_contract.py` covers the complete public catalogue, each core
  route/method and scope set, path arguments and serialized schemas. The HTTP
  test checks discovered names instead of the stale count of 16 and explicitly
  binds its public frontend/file URLs. The filename contract fixture now loads
  the actual backend fallback constant along with its isolated canonicalizer.

The 18 public tools' input/output schemas, OAuth requirements and annotations
are identical to the pre-refactoring snapshot. Models, migrations, connection
locks, outbox fencing and upload/cleanup recovery implementations are preserved.
Snapshots, schema comparison and test logs are retained in the ignored
`.mcp-validation/refactor-*` files. The results below concern local tests;
commit, push, CI, deployment and actual external-client acceptance are separate.

| Check | Current result |
|---|---|
| Full backend plus public-tool contract | **7,406 passed, 56 warnings, 229.20 s**; 19 catalogue cases are included in that count |
| Final focused public-tool contract | **19 passed, 4 warnings, 0.55 s**; overlaps the full backend run |
| Full MCP service with real Redis | **338 passed, no skips, 60.13 s** |
| Full storage with seven PostgreSQL cases | **784 passed, no skips, 3 warnings, 18.85 s** |
| Genuine Django/MCP/storage HTTP file cycle | **1 passed, 5 warnings, 9.14 s**; real OAuth, SQL, upload callbacks, attachment, completion, replay, Range, refresh and revocation; only S3 bytes use the test provider |
| Built MCP image | Smoke passed for both protocol generations and startup on port 8123; local image `pneumatic-mcp-service:refactor-20261012` |
| Static checks | Ruff and changed-file formatting passed; storage mypy passed for 81 source files; Django check passed; MCP migration drift check reported no changes |

The complete backend run uses isolated PostgreSQL 15/Redis 6.2 containers,
copied current source, `collectstatic`, `PYTHONHASHSEED=0` and four pytest
workers (`--dist loadfile`). The fixed hash seed keeps existing set-based
parametrization in the same order on every worker. The HTTP fixture pins its
public URLs; the storage unit environment omits frontend/forms URL overrides.
Temporary containers and databases are removed after verification. Earlier
failed setup attempts are superseded by the complete successful runs above.

## Subsequent frontend review — 2026-10-09

The current frontend standards review and its local validation are recorded in
[MCP frontend review](mcp-frontend-review.md). It covers the uncommitted MCP
pages, BFF, login and settings integration using the requested frontend review
and testing workflows. Its results supersede the frontend snapshot below;
backend, MCP-service and storage results below were not rerun for this review.

## Subsequent unpublished migration consolidation — 2026-10-09

At the user's request, Django's five new MCP migrations were consolidated into
`backend/src/mcp/migrations/0001_initial.py`, and storage's two new Alembic
migrations into `6ba2db086f1b_mcp_file_capabilities.py`. The services retain
separate migration graphs and databases. Previously committed migrations are
unchanged. The final schema is unchanged; no new data migration was introduced.

Separate migration validation used disposable PostgreSQL 15 and Redis 6.2
containers, without changing shared application databases:

- Django's old/new `ProjectState` values and swappable dependencies match.
  The initial migration creates all 14 MCP tables, including `published_at`,
  `required_scopes` and delegation paths of length 8192.
- The complete Django graph applies to a fresh database. MCP rollback to zero
  and reapplication preserve an ordinary account and the other tables.
- `makemigrations mcp --check --dry-run` reports no changes.
- All backend MCP tests pass on a newly created PostgreSQL test database:
  **298 passed, 4 warnings, 309.00 s**. The full backend suite was not rerun
  for this migration-only consolidation.
- Storage's actual Alembic graph applies from base, rolls back to `5ba2db086f1a`
  and reapplies successfully. Its sole head is `6ba2db086f1b`.
- PostgreSQL reflection confirms identical old/new storage columns, types,
  defaults, primary/unique/foreign keys and indexes. The consolidated downgrade
  preserves an ordinary file. All seven storage PostgreSQL regressions pass.
- The adjusted migration regression checks every MCP table's columns,
  nullability, primary keys and indexes. Ruff and formatting checks pass.

Logs and old unpublished files are retained under the ignored `.mcp-validation/`
directory (`migrations-backend-*` and `migrations-storage-*`). The full-suite
results and runtime hashes in the standards review below predate this
consolidation; they are not a new full-suite run of the rewritten migrations.
See the runbook before using these files with a database that already applied
the earlier MCP chain.

## Confirmed findings

| Finding | Required correction | Verification |
|---|---|---|
| Duplicate deliveries bypass scheduled import/publication retry time | Check queued `next_attempt_at` under the row lock; keep expired-lease recovery | Independent real-ORM backend run: 204 passed; full backend run passed |
| Idempotency errors use a nonstandard business response | Return the existing `message`, `code`, `details` format | Independent replay/error regressions passed |
| Storage PostgreSQL tests use incorrect keyword arguments | Match upload/cleanup signatures and HTTP mock arguments | Full storage run: 778 passed, including seven PostgreSQL cases |
| MCP service accepts an unserved resource path or mismatched issuer | Require exact `/mcp` and matching issuer origin | Independent final full SDK run: 325 passed |
| Token padding could exceed the credential bound; configuration parsing accepted unsafe URL text or blank secrets | Bound the entire token and reject invalid URLs/ports or blank enabled secrets without echoing inputs | SDK configuration/token regressions passed |
| MCP login could use a query credential or miss its browser OAuth binding | Use the cookie for this continuation; require the state/provider/target binding; omit bearer from HTML and telemetry | Frontend focused and full suites passed |
| Consent actions survived invalid context; transient upload reconciliation discarded its session | Hide invalid consent actions; retain uncertain upload state and reconciliation without replaying bytes | Frontend React and BFF regressions passed |
| Task/kickoff file selectors considered only direct fields | Include actual fieldset fields in target checks, scope checks and upload-reference conversion | Independent real ORM fieldset run: 24 passed; nested-field HTTP run passed |
| Public business errors were duplicated literal strings | Use canonical translatable `MSG_MCP_*` constants and a local message registry | Genuine HTTP, focused and full backend regressions passed |
| Upload reconciliation accepted mismatched ownership; deterministic IDs could collide with ordinary files | Validate command/session/record ownership and preserve ordinary records and blobs in upload/cleanup | Final storage full suite: 778 passed |
| Cancellation could outlive a fingerprint/spool operation and close its stream early | Drain background IO before closing, including repeated cancellation | Storage cancellation and real PostgreSQL regressions passed |
| CI misses changes in connected services | Include backend, storage, frontend and contract-test paths | YAML and shared trigger paths checked |
| Eager tasks can escape the genuine HTTP test | Keep real SQL publications; mock broker hints and assert exact arguments; disable and guard analytics | Final nested-file HTTP lifecycle: 1 passed, 5 warnings, 47.40 s |
| Anonymous OAuth registration and authorization have no request budget | Apply shared atomic rate control before SDK hashing or ORM writes; include HEAD in the GET budget; use explicit proxy trust | Full MCP target: 298 passed; independent focused review: 120 passed |
| A blank Redis alias breaks cache-setting overrides when MCP is disabled | Use a harmless disabled placeholder; require real shared Redis for enabled OAuth and return sanitized 503 on an unsupported store | Independent empty-URL bootstrap/cache-close check passed; final genuine HTTP passed |

## Structure and test conventions

The review checks responsibilities and call paths, rather than merging files
solely to lower their count. HTTP parsing/serialization stays in views; operations,
queries and authorization transactions belong in the existing cohesive services.
Protocol, business authorization and file-byte handling remain separate runtime
boundaries.

The seven-line MCP `scopes.py` module was absorbed into `settings.py`. The unused
backend connection helper and constructor-only session wrapper were removed.
Frontend identity and upload-token pass-through wrappers were inlined, while
duplicate handoff validation now uses the existing security helper. Django
views delegate queries and transactional decisions to existing services.
Storage lock/execute pass-through wrappers were also removed; the real
advisory lock, upload journal and core cleanup fence remain in their use cases.
No new production module was added merely to move a small helper.
The new `messages.py` has one concrete responsibility: the canonical business
error vocabulary and gettext registration required by the review standard.

Applicable checks include typed arguments, named local calls, project line
length, removal of redundant wrappers, separate test scenarios, AAA layout and
explicit mock argument assertions. ORM, managers, SQL and transactions remain
real. Shared pytest setup belongs in `conftest.py`.

Required protocol exceptions are deliberate: OAuth error bodies and SDK callback
signatures follow their external contracts. The genuine HTTP test is one complete
lifecycle acceptance scenario; its success and subsequent revocation checks must
share the same connection and file. It supplements separate API/unit scenarios.
S3 byte storage in that test is replaced with an in-memory provider.
Its file field now comes from the existing fieldset-template fixture and the
real workflow-start service, rather than a hand-created workflow field. This
keeps the nested field's actual persistence shape in the acceptance path.

## Final verification

Overlapping targeted and full test runs are reported separately and must not
be added together. The final OAuth correction passed targeted, independent,
genuine HTTP and general backend checks.

Backend: **7,378 passed, 56 warnings, 368.47 s**, using four independent
PostgreSQL worker databases, real fixtures and the actual Linux staticfiles
manifest. A legacy fieldset assertion now compares unordered membership without
assuming a tie order. Production field ordering is unchanged. Additional local
OAuth/consent/list/periodic-task coverage and all 298 MCP scenarios are included
in this final full run. Log:
`backend/.pytest_cache/review_mcp_guard_full_final.log`.
Measured production MCP coverage is 92.56% of statements and 78.29% of branches,
excluding tests and migrations. This does not claim exhaustive branch coverage.

Both nginx configurations passed 36 routing/failure/privacy/proxy-header checks.
Both Compose configurations passed validation. Root HTTP/nginx scripts pass Ruff
and formatting with `mcp/pyproject.toml` (79 columns).
The CI trigger lists share a YAML anchor, which is explicitly supported by
[GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations).

Frontend: 216 focused tests, then 1,958 tests in 258 suites and 16 snapshots.
Production webpack, source TypeScript, changed-file Prettier/ESLint and MCP CSS
Stylelint passed. Sixteen existing lint warnings and two bundle-size warnings
remain. Source-only TypeScript uses the documented `skipLibCheck` boundary.

MCP service: locked dependencies, Ruff and formatting passed. The full suite
passed 323 tests with real Redis and no skips. Splitting two remaining SDK
scenarios added two cases; the final HTTP/protocol rerun passed 239 tests. The
current full suite independently passed 325 tests with SDK/TCP/Redis and no
skips. Docker smoke passed on both protocol versions and with HEALTHCHECK on
port 8123. See [the protocol review](../mcp/REVIEW.md).

Genuine core/MCP/storage HTTP lifecycle: **1 passed, 5 warnings, 47.40 s**. The
test uses isolated PostgreSQL/Redis, the official SDK and the production FastAPI
routes. It covers nested file upload, the completion callback, attachment,
metadata, download/Range, refresh and immediate connection/ticket revocation.
Before revocation, the renewed ticket is proved usable. The test includes the
real shared OAuth Redis budget. Runtime, root test and helper hashes for 1,196
Python files were unchanged through this run, digest
`64e2c4f06f2ca71ff1f1bd99c006befb6294c5dc1ef7fb66efb3db941406f158`.
Its log is `.mcp-validation/review-http-files-stable-final.log`; before/after
manifests are saved alongside it.

The independent frontend/protocol/fieldset pass found no open confirmed defect:
216 frontend tests, 325 MCP tests and 24 real-ORM fieldset cases passed.
The subsequent backend/storage review also found no open confirmed defect:
204 backend MCP tests (including two additional real-ORM reproductions), 241
storage API/PG/auth/filename cases and 49 URL-import cases passed without skips.
It rechecked the three initial findings, auth/revocation, file scopes, outbox
and leases, cancellation, crash journals and cleanup/retry preservation.
Final general full-suite results are recorded separately; targeted counts
overlap and must not be added together.

The final independent OAuth review passed **120 tests in 44.32 s**, without
skips. It checked atomic shared budgets under concurrency, counter saturation,
unchanged refusal TTL, HEAD/GET sharing, trailing slash handling, trusted TCP
and Unix proxy chains, no SQL/hash work after denial, OAuth 429/503 headers,
PKCE/DCR success, and disabled-feature cache closure with empty Redis URLs.
All 298 backend MCP cases passed together in the preceding target run
(20 warnings, 36.47 s). No confirmed issue remains in the reviewed scope.

Storage: **778 passed, 3 warnings, 25.27 s**, including seven real PostgreSQL
concurrency/crash/migration cases. The final 28 added cases close the remaining
local matrix gaps. Ruff, a separate forced argument-annotation check, formatting
for 28 changed Python files, mypy on 79 source files and Poetry lock validation
passed. Subsequent LF/CRLF normalization had an identical AST. See
[the storage lifecycle review](../storage/docs/mcp-lifecycle-review.md).
Only the external S3/live DNS/TLS acceptance remains outside this matrix.

See [the original implementation report](mcp-verification.md) for the baseline,
[the backend test matrix](../backend/docs/mcp-review-tests.md) for dependencies
and scenarios, and [the rollout runbook](mcp-runbook.md) for external acceptance.

Local review does not establish deployed compatibility with Claude.ai or ChatGPT,
external SSO, production S3 or downstream notification delivery.

The subsequent [MCP middleware cleanup](../mcp/REVIEW.md#middleware-cleanup--2026-10-12)
removes diagnostic routes and duplicate transport checks, separates necessary
middleware responsibilities and records its final local verification.
