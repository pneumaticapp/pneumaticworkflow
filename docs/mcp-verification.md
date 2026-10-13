# MCP implementation verification — 2026-10-09

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

This is the implementation baseline. Subsequent standards review changed the
uncommitted feature and added regressions; its current results are recorded in
[MCP standards review](mcp-review.md) and the subsequent
[MCP frontend review](mcp-frontend-review.md). The middleware cleanup and its
current verification are recorded in [the MCP service review](../mcp/REVIEW.md).
Counts below belong to the earlier run.

The logical refactoring on 2026-10-12 is documented in
[MCP standards review](mcp-review.md#logical-refactoring-2026-10-12).

The implementation and local verification are complete on branch
`backend/mcp/50712__add_mcp`. This report records the local verification results.
There has been no push, GitHub Actions run, deployment or acceptance test inside
Claude.ai or ChatGPT.

The public endpoint is configured as `https://my.pneumatic.app/mcp`. A separate
private MCP container serves Streamable HTTP behind the existing nginx. Django
remains the authorization and business server; the existing file service keeps
uploads, downloads and byte storage. No Python/Django framework migration was
introduced by this change: this checkout already uses Python 3.12 and Django 5.2.

## Delivered scope

- Eighteen tools cover templates, workflows, tasks, comments and the file lifecycle.
- OAuth authorization code with S256 PKCE, CIMD/DCR, resource binding, scope
  consent, refresh rotation and connection revocation uses existing user login.
- Business operations use short-lived, narrowly bound internal delegations.
  External OAuth tokens are not forwarded to business or file endpoints.
- Transactional idempotency and a durable publication outbox cover mutations and
  subsequent background work. URL imports have durable leases and account limits.
- Browser uploads, attachment without task completion, bounded URL imports,
  protected download/Range tickets and interrupted-upload cleanup use the
  separate file service.
- Docker/Compose, nginx/Railway routing, feature-off defaults,
  CI validation and rollout/recovery documentation are included.

Locked dependency changes include `django-oauth-toolkit==3.4.1` in the backend,
`mcp==2.3.0` / `mcp-types==2.3.0` in the new service, and direct
`httpcore==1.0.9` in storage. The unpublished migration chains were consolidated
after this baseline run. Deployment now requires one Django MCP migration,
`mcp.0001_initial`, the toolkit's migrations and one storage Alembic migration.
Storage's new head is `6ba2db086f1b`; the resulting schema is unchanged.

## Final local results

Counts describe separate test runs; targeted tests overlap full suites.

| Area | Result | Evidence and limits |
|---|---|---|
| Backend full suite | 7,214 passed, 56 warnings, 352.77 s | Real PostgreSQL/ORM; final source including comment and ACL outbox fixes |
| Backend targeted checks | 111 auth/outbox and 47 OpenAPI tests passed | Django check, applied migrations, MCP migration check, Ruff and lock check passed; schema has zero errors and zero MCP warnings |
| MCP service | 222 passed, no skips | Locked dependencies, Ruff/format; built-image HTTP smoke covers both supported protocol generations; diagnostic routes from this baseline were subsequently removed |
| Frontend full suite | 258 suites, 1,922 tests, 16 snapshots passed | Production build and source TypeScript with `--skipLibCheck` passed; changed files pass ESLint/Prettier |
| Storage full suite | 718 passed, no skips | Includes seven real-PostgreSQL tests, Alembic upgrade/downgrade, concurrency and abrupt process termination |
| Storage final auth regression | 121 relevant tests passed | Run after the final Unicode service-header fix; full 718-test run predates this small fix; Ruff/format, mypy and lock check passed |
| Actual core/MCP/storage HTTP cycle | 1 passed, 5 warnings, 136.71 s | Real Django OAuth and business views, SDK HTTP transport and FastAPI/PostgreSQL storage; only S3 bytes replaced with memory |
| Nginx | 34 checks passed | Both configurations: 20 routing and 14 failure/privacy checks using Docker upstreams |
| Packaging | Passed | Both Compose configurations, nginx parser, shell checks and `git diff --check` |

The genuine HTTP cycle verifies DCR, PKCE, consent/issuer, reads, workflow start,
idempotent replay, comment, upload acknowledgement, attachment, task completion,
file metadata, ticket download and Range. After refresh it obtains a new ticket
and first proves that download succeeds; connection revocation then denies that
same ticket and MCP access. This avoids mistaking an already expired ticket for
successful revocation enforcement.

Local logs are retained under `.mcp-validation/` and `backend/tmp/`, both ignored
by Git. The backend full-run command was:

```text
pytest src -n 4 --dist loadfile --reuse-db --ds=src.settings --dc=Testing --tb=short -q
```

HTTP, image and nginx test setup is documented in
[the runbook](mcp-runbook.md#local-verification).

## Review outcome and existing baseline

Repeated implementation and independent reviews found and corrected authorization,
scope upgrade, permission replay, file naming/path, upload recovery, URL import,
logging, consent/upload UI and durable dispatch defects. The final independent
reviews have no remaining confirmed MCP findings.

Existing repository issues remain outside this change: frontend strict library
declaration checking reports duplicate React types in dependencies; repository-wide
format checking reports existing formatting; the frontend build retains bundle
size warnings. The backend's global migration-generation check reports existing
drift in unchanged `accounts`, `logs`, `processes` and `permissions` definitions,
and the existing OpenAPI schema retains unrelated warnings. Applied migrations
and MCP-specific migration generation checks pass. These results do not establish
that all repository-wide checks are clean.

## Release work still requiring external evidence

The inspected Railway project has production only and no MCP service. An isolated
staging environment and the private MCP service must be provisioned, environment
secrets configured, migrations applied and changes deployed in the order in
[the rollout runbook](mcp-runbook.md#release-order).

Actual Claude.ai and ChatGPT account connection, external SSO, production object
storage and downstream notification delivery have not been verified. Those checks
must precede a limited production pilot. Passing local tests, protocol smoke tests,
consent or health endpoints do not substitute for that acceptance evidence.

See [the design](mcp-design.md) and
[the backend API contract](../backend/docs/mcp-api.md) for implementation details.
