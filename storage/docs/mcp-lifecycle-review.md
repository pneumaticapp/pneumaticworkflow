# MCP storage lifecycle review

The subsequent extraction of import and download-ticket use cases is documented
in [MCP standards review](../../docs/mcp-review.md#logical-refactoring-2026-10-12).
The hashes and counts in this lifecycle review belong to its earlier revision.

Scope: `storage/**`, reviewed against the complete `backend-revue.md` and
`backend-tests.md` workflows on 2026-10-09. No commits, pushes, deployments,
root hook changes, or changes to shared Docker services.

After this lifecycle review, the two unpublished MCP Alembic migrations were
consolidated into `6ba2db086f1b`. Its upgrade includes the recovery journal and
its downgrade removes all three MCP tables. See `docs/mcp-review.md` for the
separate migration validation; the full-suite evidence below predates it.

## Confirmed defects fixed

- Reject a command whose user/account differs from its delegated session
  before hashing, journal creation, storage writes, or core calls.
- Check the owner of the real file record when reconciling a completed
  import. A mapping alone does not authorize a different owner's record.
- Refuse a deterministic MCP file ID already occupied by an ordinary file.
  Failed-upload cleanup also checks ordinary records before deleting blobs.
- Drain the fingerprint reader and temporary-file writer on cancellation,
  including repeated cancellation, before their caller can close the stream.
- Use storage's normal error catalog for core outages, upload conflicts and
  unsafe imports; hide foreign-account MCP resources with 404.
- Repair PostgreSQL regressions: upload `command`/`user` arguments, cleanup
  override `user`, and core callback `path`/`body` mock assertions. Concurrent
  requests own separate streams.

## Structural changes

Removed the upload service's lock pass-through and the cleanup service's
execute pass-through. Shared request/database fixtures live in the existing
fixture modules; command, service and user fixtures return their objects
directly. Tests no longer import helpers from other test modules. No new
production wrapper or production module was added by this review.

Authentication, file services, transport and route boundaries remain
separate. The advisory transaction lock, durable upload journal, core
cleanup fence and audit-before-callback ordering remain intact.

## Dependency graph

Functions are listed from leaves towards their callers below the graph.

```text
MCP storage entry points
|-- authenticate_mcp_request
|   |-- _request_credential / _require_flat_read_path
|   `-- MCPCoreClient.validate
|       |-- MCPCoreClient.post -> private core HTTP
|       `-- FileGrant.model_validate / FileGrant.user
|-- upload_file / import_file
|   |-- MCPUploadService.execute
|   |   |-- _fingerprint -> request stream
|   |   |-- _journal_attempt / _claim -> real ORM
|   |   |-- lock_upload_session -> PostgreSQL advisory lock
|   |   |-- _revalidate -> MCPCoreClient.validate
|   |   |-- _store -> object storage + real ORM
|   |   `-- _protected_cleanup -> _cleanup_failed_upload
|   |-- MCPUploadService.complete -> revalidation + private core callback
|   |-- RequestEvents.file_upload -> audit side effect
|   `-- import_file
|       |-- MCPUploadService.find_completed -> real ORM + owner check
|       `-- URLImporter.download
|           |-- _download
|           |   |-- validate_url
|           |   |-- resolve_public_ip -> is_public_address + DNS
|           |   `-- PinnedNetworkBackend.connect_tcp -> numeric dial + TLS
|           `-- _read_response -> bounded temporary-file writes
|-- get_metadata / create_ticket -> _metadata -> file service
|-- download_ticket -> real ticket ORM + live core -> download_file
|-- cleanup_uploads -> MCPCleanupService.execute
|   `-- _cleanup_one / _cleanup_attempt
|       |-- lock_upload_session / real ORM provenance checks
|       |-- private core terminal fence
|       `-- object deletion / real ORM deletion
|-- MCPUploadLimitMiddleware.__call__ -> ASGI byte admission
`-- RedactionFilter.filter / sentry_before_send -> redact_text / redact_data
```

Leaves: `validate_url`, `is_public_address`, `_fingerprint`,
`lock_upload_session`, `FileGrant.user`, `_request_credential`,
`_require_flat_read_path`, `redact_text`, `redact_data`.

Infrastructure and intermediate functions: `resolve_public_ip`,
`PinnedNetworkBackend.connect_tcp`, `URLImporter._read_response`,
`URLImporter._download`, `URLImporter.download`, `MCPCoreClient.post`,
`MCPCoreClient.validate`, `MCPUploadService._revalidate`, `_journal_attempt`,
`_claim`, `_store`, `_cleanup_failed_upload`, `_protected_cleanup`,
`find_completed`, `MCPCleanupService._cleanup_one`, `_cleanup_attempt`,
`_metadata`, `RedactionFilter.filter`, `sentry_before_send`.

Callers: `authenticate_mcp_request`, `MCPUploadService.execute`, `complete`,
`MCPCleanupService.execute`, `upload_file`, `import_file`, `get_metadata`,
`create_ticket`, `download_ticket`, `cleanup_uploads`,
`MCPUploadLimitMiddleware.__call__`.

## Mock boundaries

| Boundary | Test implementation |
| --- | --- |
| Private core HTTP | Named mock with explicit `path`/`body`, or real httpx client with MockTransport |
| Object upload/delete | Named async mock with bucket, path, stream and MIME assertions |
| Audit and ordinary authentication | Named side-effect mocks, including forbidden-call assertions |
| DNS/TCP | Named mock backend with real httpcore HTTP parser and explicit numeric dial/TLS arguments |
| SQL/ORM/transactions | Real SQLAlchemy sessions; SQLite for route tests and PostgreSQL for concurrency/crash tests |
| Database failure injection | Real transaction events and a real duplicate insert; no mocked ORM methods or transaction managers |
| Abrupt process death | Child exits after a local object write; parent recovers its durable PostgreSQL journal |

`ANY` is used for request-owned streams and authentication/command objects
created inside ASGI. Blob bytes, file metadata, record ownership and core
callback provenance have separate concrete assertions. No real S3 requests
are made.

The filename fixture executes the actual `canonical_filename` function
definition from the shared backend source. It extracts that pure function
and its `re` import using AST, rather than importing backend's `src` package
into storage's conflicting `src` namespace. This also avoids requiring
Django just because backend error messages now use Django translation.

## Test cases

`Yes` means a corresponding storage test runs; it does not mean every
possible input or external provider behavior is covered.

| Function | Test cases | Annotation | Test |
| --- | --- | --- | --- |
| `require_enabled_mcp_config` | Disabled/default settings; short/empty secret; private/malformed origin; hard size cap; secret-safe messages | Parametrized configuration unit | Yes |
| `validate_url` | HTTP, credentials, controls, fragments, alternate ports and malformed hosts | Parametrized unit | Yes |
| `is_public_address` | Public v4/v6; private, special-use and IPv6 transition addresses | Parametrized unit | Yes |
| `resolve_public_ip` | Mixed DNS answers; rebinding after redirect | Real address validation | Yes |
| `connect_tcp` | Numeric pinned dial; original/IDNA SNI; certificate verification; no ambient proxy/auth | Real HTTP parser, fake wire | Yes |
| `download` | Unsafe redirects; fourth redirect; compressed body; declared and streamed byte limits | Parametrized unit | Yes |
| `download` | DNS stall consumes the overall deadline | Cancellation unit | Yes |
| `download` | Single/repeated cancellation during a blocked spool write drains before close | Thread synchronization | Yes |
| `URLImporter.__init__` | Requested limit cannot raise the hard cap | Default/boundary unit | Yes |
| `URLImporter.__init__` | Zero/negative limit with exact error message | Direct constructor boundary | Yes |
| `_read_response` | Non-200 status, empty/undefined/fractional/negative length; omitted optional headers | Real response and stream | Yes |
| `_fingerprint` | Real binary bytes, metadata and idempotency; repeated cancellation waits for reader | Route/service regression | Yes |
| `FileGrant.user` | Delegation and source-expiry provenance reach authenticated user | Unit | Yes |
| `MCPCoreClient.post` | Private service auth, no environment proxy, timeout, 401/403/5xx/redirect | Unit | Yes |
| `MCPCoreClient.post` | Invalid JSON; array/null/string/number/boolean JSON; private-core 409 sanitization | Real httpx MockTransport | Yes |
| `MCPCoreClient.validate` | Inactive/malformed identity, wrong operation/connection and invalid expiry | Parametrized unit | Yes |
| `authenticate_mcp_request` | No ordinary-auth fallback, forged sessions, canonical raw/encoded paths and mounted root paths | Route/unit | Yes |
| `_require_file_service` / `_require_mcp` | Wrong/Unicode service secret and ordinary-user access to MCP routes | Route | Yes |
| `execute` | Command owner differs from delegated user/account; no write or journal | Real ORM regression | Yes |
| `_claim` | Ordinary file collision preserves its record and blob | Real ORM regression | Yes |
| `execute` | Same content retry; different content conflict; ordinary/MCP cap | Route | Yes |
| `execute` | Real duplicate flush; partial storage failure; failed cleanup retains durable journal | Real SQL fault injection | Yes |
| `execute` | Two concurrent uploads create one committed object and mapping | Real PostgreSQL | Yes |
| `execute` | Commit failure deletes orphan object and rolls back mapping | Real PostgreSQL | Yes |
| `_cleanup_failed_upload` | Late failed writer cannot erase a committed retry | Real PostgreSQL | Yes |
| `_protected_cleanup` | Single/repeated cancellation waits for deletion before reraising | Real PostgreSQL | Yes |
| `complete` | Lost callback reply reconciles without duplicate object or audit | Upload/import parametrization | Yes |
| `find_completed` | Mapping/file owner mismatch is denied | Real ORM regression | Yes |
| `find_completed` | Missing real file returns a sanitized outage; mapping retained and no side effects | Real ORM consistency branch | Yes |
| `import_file` | Private service secret, Unicode auth denial, safe error response | Route | Yes |
| `import_file` | Grant revoked/changed/expired after fetch closes stream without storage write | Route regression | Yes |
| `import_file` | Completed retry performs no second external fetch | Route | Yes |
| `get_metadata` | Raw legacy IDs; unsafe IDs denied; foreign account hidden | Route | Yes |
| `create_ticket` | Hash only, authorization binding, source-clamped and positive subsecond TTL | Real ticket ORM | Yes |
| `download_ticket` | Full/Range request; local expiry; live revocation/identity/authorization changes | Real ticket ORM + route | Yes |
| `cleanup_uploads` | Distinct private secret; absent/default request body; core outage | Route | Yes |
| `_cleanup_one` | Eligible MCP deleted; ordinary file preserved; ticket deletion; recent file skipped | Real ORM route | Yes |
| `_cleanup_attempt` | Ordinary record or committed winner prevents orphan deletion | Real ORM route | Yes |
| `execute` (cleanup) | Strict eligible boolean, hourly recheck backoff, completed retry, storage/commit failure retry | Real ORM route | Yes |
| `execute` (cleanup) | Crash-surviving journal recovers after abrupt process exit | Real PostgreSQL + child | Yes |
| `execute` (cleanup) | Default/floor/max cap over 103 mixed candidates; timeout cancellation rolls back without delete | Real ORM and real Timeout | Yes |
| Migration upgrade/downgrade | Capabilities/journal roundtrip preserves ordinary file; columns/index verified | Real PostgreSQL | Yes |
| Filename contract | Actual backend canonicalizer; upload/import callback and metadata agree on spaced/Unicode names | Shared-source contract | Yes |
| ASGI upload admission | Chunked request stops before reading its entire body | Real ASGI | Yes |
| Redaction | Ticket, credential, signed query, validation input, nested Sentry and real uvicorn argument shape | Unit | Yes |
| Provider integration | Live S3 behavior and real public DNS/TLS endpoint | Outside this isolated run | No |

## Annotation and protocol exceptions

The project explicitly forbids `-> None` on procedures, including test
helpers. Ruff's return-annotation rules and mypy's `no-untyped-def` also
require those annotations. Procedure definitions therefore have only the
necessary `ANN201`, `ANN202` or `ANN204` suppression. Affected modules disable
only mypy's aggregate `no-untyped-def` diagnostic; body checking and argument
annotation checks remain enabled. The nested no-argument cleanup coroutine
has one `no-untyped-call` suppression for this same conflict.

A separate Ruff run forces `ANN001,ANN002,ANN003` with per-file ignores
cleared across all source and MCP tests/helpers. An AST audit also checks
argument annotations of the MCP additions in shared fixtures. These checks
prevent the return convention from concealing untyped arguments. Root
pre-commit configuration remains strict.

ASGI/httpcore callbacks and Python/library positional or variadic APIs keep
their required calling conventions; owned service parameters are named.
Storage uses FastAPI/Pydantic validation and its existing error envelope,
not Django serializers. OAuth/SDK protocol errors belong to the backend
review and must retain their standard protocol contract.

## Validation evidence

Own container: `review-mcp-storage-20261009-6f31` on `pneu-test`, with read-only
checkout mounts. Own database: `review_mcp_storage_20261009_6f31`; every
PostgreSQL test creates/drops only its own UUID schema. Redis DB 14 uses the
`review_mcp_6f31:` prefix. Shared containers/state were not deleted or reset.

- Full suite: **778 passed, 3 warnings, 25.27 seconds**, including all seven
  real PostgreSQL scenarios, with `MCP_TEST_DATABASE_URL` set to the own DB.
- Ruff lint: entire `storage/src storage/tests` passed.
- Forced argument-annotation Ruff check: passed.
- Mypy: **79 source files**, no issues.
- `poetry check --lock`: exit 0; existing Poetry metadata deprecation warnings.
- Parent-reported genuine core/storage HTTP cycle: **1 passed, 5 warnings,
  54.71 seconds**, including private auth, callback, PostgreSQL, upload,
  download Range and revocation, with only object storage in memory.

After that full suite/HTTP run, formatter-only normalization removed mixed
LF/CRLF endings in `di/container.py`, `exceptions/error_codes.py`, and
`exceptions/error_messages.py`. The formatter diff contained no code/token
changes. The exact pre-format bytes were reconstructed and verified against
the previously recorded SHA-256 values; parsing before/after produced
identical ASTs. This changes raw file hashes, not runtime behavior.

Commands inside the own container (the PostgreSQL URL is injected privately):

```sh
python -m pytest -c /repo/storage/pyproject.toml /repo/storage/tests \
  -q -o addopts= --tb=short -p no:cacheprovider \
  --basetemp=/tmp/pytest-review-mcp-final-16
ruff check --no-cache --config storage/ruff.toml storage/src storage/tests
ruff check --select ANN001,ANN002,ANN003 --config storage/ruff.toml \
  --config 'lint.per-file-ignores={}' storage/src <MCP-tests-and-helpers>
ruff format --check --config storage/ruff.toml <28-changed-Python-files>
mypy --config-file mypy.ini --cache-dir /tmp/mypy-review-final src
poetry check --lock
```

The 28 added local cases close every local `No` row previously recorded in
this matrix. Constructor and response tests check errors before stream
writes; core tests use a real client/parser instead of mocked magic methods.
The missing-file scenario performs a real ORM delete. Candidate cap tests
seed 51 orphan attempts and 52 committed mappings, checking the combined
queue, exact core calls and persisted backoff counts for default, floor and
maximum limits.

The cleanup timeout test replaces only that module's `asyncio` dependency
binding. Its real `asyncio.Timeout` is rescheduled to expire after entering
the core await, so it is independent of database/machine speed. The global
clock and the actual `asyncio` module are unchanged. Real transaction
rollback preserves the file/mapping and no object deletion runs.

Ruff commands run from `/repo`; mypy/Poetry run from `/repo/storage`.
Pytest runs from `/tmp` to avoid loading checkout secrets from `.env`.
Uncovered paths in the table remain explicit; this is not a claim of
exhaustive branch coverage or live object-provider validation.

## Changed paths in this review

Relative to `storage/`; pre-existing MCP changes elsewhere are preserved.

```text
src/application/use_cases/mcp_cleanup.py
src/application/use_cases/mcp_upload.py
src/infra/url_importer.py
src/presentation/api/files.py
src/presentation/api/mcp_files.py
src/shared_kernel/auth/mcp.py
src/shared_kernel/database/migrations/versions/6ba2db086f1b_mcp_file_capabilities.py
src/shared_kernel/di/container.py
src/shared_kernel/exceptions/error_codes.py
src/shared_kernel/exceptions/error_messages.py
src/shared_kernel/exceptions/mcp_exceptions.py
src/shared_kernel/middleware/mcp_upload_limit.py
tests/api/test_mcp_cleanup.py
tests/api/test_mcp_files.py
tests/api/test_mcp_upload_regressions.py
tests/fixtures/common.py
tests/fixtures/integration.py
tests/fixtures/unit.py
tests/integration/mcp_crash_upload.py
tests/integration/test_mcp_filename_contract.py
tests/integration/test_mcp_postgres.py
tests/live_mcp_server.py
tests/unit/test_mcp_auth.py
tests/unit/test_mcp_config.py
tests/unit/test_mcp_redaction.py
tests/unit/test_mcp_upload_limit.py
tests/unit/test_url_importer.py
docs/mcp-lifecycle-review.md
```

Final individual SHA-256 values after formatter normalization:

```text
src/shared_kernel/di/container.py
3de078b0e4879626d41405851922f1da43f8574a42513b4a6eb24df8cad58fac
src/shared_kernel/exceptions/error_codes.py
a69e14db3c0693ce447de4b5b4e8ef6e32bc35b0389dde6946e356e06ee65c27
src/shared_kernel/exceptions/error_messages.py
2dfec600a219528438e3703fea1c26652875bce9a92c6f4890671cfbecfae5ec
tests/live_mcp_server.py
5d0180d0c9e1d63bfcc8abb749a83c18e60725efe1e8442f07b0978acf90c6c4
```

These are individual file hashes, not the parent's combined snapshot hash.
