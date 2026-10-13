# MCP backend review and test matrix

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

Scope: uncommitted backend MCP implementation and its changed integration
paths, reviewed against `backend-revue.md` and `backend-tests.md` in
`D:/Dev/knowledge/.agent/workflows/`. HEAD remains `3d6a407d9`.
During the standards review, no migration was merged or rewritten. A subsequent
user-requested change consolidated the five unpublished MCP migrations into
`0001_initial`; see `docs/mcp-review.md` for its separate validation. No migration
was reapplied to a shared application DB. The full-suite results and source
hashes below describe the standards review before that consolidation.

## Local import audit — 2026-10-12

The audit inspected function-local imports added by the uncommitted Python
changes: seven in runtime code and four in the isolated storage HTTP helper.

- `MCPConfig`: `CommitAwareTask` is a module import; task publication loads
  in `ready()` after model initialization. Authentication schema registration
  moved to `AuthConfig.ready()` on 2026-10-13. Cold-process probes verify both
  application configs import before models and register hooks without SQL.
  This follows
  [Django's application startup contract](https://docs.djangoproject.com/en/5.2/ref/applications/#django.apps.AppConfig.ready).
- `ImportService.process`: the task module imports `ImportService` itself;
  its reverse `storage_post` dependency remains deferred to avoid a cycle.
- Storage authentication: MCP auth imports `AuthUser` from its middleware;
  the reverse import in `try_authenticate` remains deferred for the same reason.
- MCP `MCPError` moved to a module import; it has no application initialization
  dependency.
- The storage HTTP helper's `get_settings` and `sanitize_content_type` moved
  to module imports. App and DI imports remain after explicit test environment
  setup and the isolated working directory, since they initialize settings.
  Its blanket `PLC0415` suppression was replaced by two targeted suppressions.

Each retained runtime import now has its concrete reason beside the code.
Validation: three real cold-process Django regressions pass, covering config
import before models and enabled/disabled startup, outbox wiring and actual
authentication-extension matching. A guard forbids database connections during
startup. Both MCP protocol/HTTP files pass: **245 tests, 55.77 s**. Importing the
storage helper leaves the settings cache empty. Ruff and formatting checks pass.
Full backend/storage suites and the live three-service cycle were not rerun for
these import-only changes; their earlier results below remain historical.

## Tested dependency graph

The HTTP layer validates/serializes input and calls existing cohesive services.
Permission, billing, SQL, transaction and token checks run against the real ORM.
The tree lists the business dependencies; DOT/oauthlib own protocol validation.

```text
Public OAuth AS -> OAuthThrottleMiddleware -> CustomSimpleRateThrottle
|-- POST register -> REGISTER budget
|-- GET/HEAD authorize + login -> AUTHORIZE budget
|-- POST token + revoke -> TOKEN budget
|-- _client_ip -> socket peer / explicitly trusted proxy chain
`-- _rate_limit_response -> shared Redis atomic Lua / bounded TTL
HTTP/API -> authentication.McpDelegationMiddleware
         -> mcp.McpExecutionMiddleware
|-- AuthorizationView / LoginCodeView / LoginCompleteView / ConsentView
|   `-- consent.create_authorization_request / create_login_code /
|       consume_login_code / get_context / approve_request
|       |-- get_bound_request -> AuthorizationRequest row lock
|       |-- LoginCode / User / Account live identity checks
|       `-- DOT OAuthLibMixin -> MCPValidator -> CodeBinding / Connection
|-- MCPTokenView -> oauth.token_connection -> lock_connection_group
|   `-- MCPValidator.validate_code / validate_refresh_token /
|       _save_bearer_token -> AccessBinding / RefreshBinding
|-- RegistrationView / RegistrationManagementView
|   `-- oauth.registration_error / save_registered_client /
|       public_registration_response -> ClientPolicy + DOT
|-- ConnectionsView / ConnectionRevokeView
|   `-- services.list_connections / revoke_connection
|       `-- lock_connection_group -> real token/delegation revocation
|-- IntrospectionView / DelegationView / DelegationAuthentication
|   `-- services.introspect / delegate / get_delegation
|       |-- get_access_binding / is_live_connection -> live ORM identity
|       `-- operations.get_operation -> file_metadata.decode_file_segment
|-- UploadCreateView / UploadStatusView / UploadTokenView
|   `-- uploads.create_session / get_session / create_upload_token
|       |-- serialize_session / issue_upload_capability
|       `-- check_session_target -> get_task_field / get_kickoff_field
|           `-- get_kickoff / billing / real permissions and soft-delete
|-- UploadImportView / UploadAttachView -> authorize_upload_replay
|   `-- queue_import / attach_upload -> row locks + real mutation
|-- FileValidationView / UploadCompletionView / UploadCleanupView
|   `-- validate_files / complete_upload / authorize_cleanup
|       `-- get_upload_capability / AttachmentService / live token bindings
|-- TemplateViewSet.run / TaskViewSet.complete / delegated comments
|   |-- prepare_run_payload / prepare_complete_payload / check_write_files
|   |   `-- require_file_scopes / check_complete_file_scopes / get_session
|   `-- real business services -> CommitAwareTask.apply_async
|       |-- schedule_task_publication -> real transaction/on_commit
|       `-- TaskPublication SQL row -> publication hint (mocked transport)
|-- tasks.import_upload / publish_notification
|   |-- locked retry schedule and lease -> fenced outcome write
|   `-- storage_post / task.apply_async (external effects mocked)
|-- dispatch_pending_imports / dispatch_pending_notifications / cleanup_uploads
|   `-- due ORM selections -> mocked external task/HTTP delivery
`-- prune_expired_state / redact_event / schema
    `-- bounded ORM cleanup / recursive redaction / schema contracts
```

## Function inventory, leaves first

All locally defined functions below are ordered after their statically resolved
MCP dependencies. SDK dispatch, callbacks and recursive closures are represented
by their owning method; ORM/framework internals are not separate test targets.

| Function | Source line | Local MCP dependencies |
|---|---:|---|
| `apps.MCPConfig.ready` | 10 | Schema and task hook registration |
| `file_metadata.valid_file_id` | 8 | Leaf (ORM/SDK/builtins only) |
| `file_metadata.encoded_file_id` | 23 | `file_metadata.valid_file_id` |
| `file_metadata.decode_file_segment` | 29 | `file_metadata.encoded_file_id` |
| `operations.get_operation` | 121 | `file_metadata.decode_file_segment` |
| `services.digest` | 55 | Leaf (ORM/SDK/builtins only) |
| `services.is_live_connection` | 59 | Leaf (ORM/SDK/builtins only) |
| `services.get_delegation` | 181 | `operations.get_operation`, `services.digest`, `services.is_live_connection` |
| `authentication.DelegationAuthentication.authenticate` | 91 | `services.get_delegation` |
| `authentication.DelegationAuthentication.authenticate_header` | 111 | Leaf (ORM/SDK/builtins only) |
| `authentication.LoginTokenAuthentication.authenticate_credentials` | 70 | Leaf (ORM/SDK/builtins only) |
| `authentication.ServiceAuthentication.authenticate` | 18 | Leaf (ORM/SDK/builtins only) |
| `authentication.ServiceAuthentication.authenticate_header` | 37 | Leaf (ORM/SDK/builtins only) |
| `authentication.StorageAuthentication.authenticate` | 42 | Leaf (ORM/SDK/builtins only) |
| `authentication.StorageAuthentication.authenticate_header` | 65 | Leaf (ORM/SDK/builtins only) |
| `consent.get_bound_request` | 100 | Leaf (ORM/SDK/builtins only) |
| `consent.create_login_code` | 146 | `consent.get_bound_request`, `services.digest` |
| `consent.approve_request` | 172 | `consent.create_login_code`, `consent.get_bound_request` |
| `consent.consume_login_code` | 49 | `services.digest` |
| `consent.create_authorization_request` | 24 | Leaf (ORM/SDK/builtins only) |
| `consent.get_context` | 126 | `consent.get_bound_request` |
| `file_metadata.canonical_content_type` | 99 | Leaf (ORM/SDK/builtins only) |
| `file_metadata.canonical_filename` | 93 | Leaf (ORM/SDK/builtins only) |
| `uploads.require_file_scopes` | 150 | Leaf (ORM/SDK/builtins only) |
| `uploads.check_complete_file_scopes` | 801 | `uploads.require_file_scopes` |
| `uploads.check_write_files` | 914 | `uploads.require_file_scopes` |
| `middleware.DelegationMiddleware._authorize_replay` | 230 | `uploads.check_complete_file_scopes`, `uploads.check_write_files` |
| `services.lock_connection_group` | 257 | Leaf (ORM/SDK/builtins only) |
| `middleware.DelegationMiddleware._execute_idempotently` | 270 | `authentication.DelegationAuthentication.authenticate`, `middleware.DelegationMiddleware._authorize_replay`, `services.lock_connection_group` |
| `middleware.DelegationMiddleware.__call__` | 184 | `authentication.DelegationAuthentication.authenticate`, `middleware.DelegationMiddleware._execute_idempotently` |
| `middleware.DelegationMiddleware.__init__` | 181 | Leaf (ORM/SDK/builtins only) |
| `models.MCPModel.__str__` | 11 | Leaf (ORM/SDK/builtins only) |
| `oauth.MCPValidator._load_application` | 47 | Leaf (ORM/SDK/builtins only) |
| `oauth.MCPValidator._save_bearer_token` | 243 | `services.digest` |
| `services.revoke_connection` | 224 | `services.lock_connection_group` |
| `oauth.MCPValidator.revoke_token` | 271 | `services.digest`, `services.revoke_connection` |
| `oauth.MCPValidator.save_authorization_code` | 99 | `services.digest`, `services.is_live_connection` |
| `oauth.MCPValidator.validate_code` | 172 | `services.digest`, `services.is_live_connection` |
| `oauth.MCPValidator.validate_grant_type` | 78 | Leaf (ORM/SDK/builtins only) |
| `oauth.MCPValidator.validate_refresh_token` | 206 | `services.digest`, `services.is_live_connection`, `services.revoke_connection` |
| `oauth.MCPValidator.validate_response_type` | 60 | Leaf (ORM/SDK/builtins only) |
| `oauth.get_token_connection_id` | 293 | `services.digest` |
| `oauth.public_registration_response` | 339 | Leaf (ORM/SDK/builtins only) |
| `oauth.registration_error` | 315 | Leaf (ORM/SDK/builtins only) |
| `oauth.save_registered_client` | 351 | `oauth.public_registration_response` |
| `oauth.token_connection` | 34 | `oauth.get_token_connection_id`, `services.lock_connection_group` |
| `redaction.redact_event` | 42 | Leaf (ORM/SDK/builtins only) |
| `schema.MCPDelegationScheme.get_security_definition` | 24 | Leaf (ORM/SDK/builtins only) |
| `schema.MCPLoginTokenScheme.get_security_definition` | 10 | Leaf (ORM/SDK/builtins only) |
| `serializers.FileValidationSerializer.validate_file_id` | 126 | `file_metadata.valid_file_id` |
| `serializers.UploadSerializer.validate` | 81 | Leaf (ORM/SDK/builtins only) |
| `serializers.UploadSerializer.validate_content_type` | 73 | `file_metadata.canonical_content_type` |
| `serializers.UploadSerializer.validate_filename` | 70 | `file_metadata.canonical_filename` |
| `serializers.UploadSerializer.validate_size` | 76 | Leaf (ORM/SDK/builtins only) |
| `services.get_access_binding` | 78 | `services.digest`, `services.is_live_connection` |
| `services.delegate` | 124 | `operations.get_operation`, `services.digest`, `services.get_access_binding` |
| `services.introspect` | 106 | `services.get_access_binding` |
| `services.list_connections` | 28 | Leaf (ORM/SDK/builtins only) |
| `tasks.storage_post` | 32 | Leaf (ORM/SDK/builtins only) |
| `tasks.cleanup_uploads` | 265 | `tasks.storage_post` |
| `tasks.dispatch_pending_imports` | 183 | Leaf (ORM/SDK/builtins only) |
| `tasks.dispatch_pending_notifications` | 249 | Leaf (ORM/SDK/builtins only) |
| `uploads.check_billing` | 169 | Leaf (ORM/SDK/builtins only) |
| `uploads.get_kickoff` | 66 | Leaf (ORM/SDK/builtins only) |
| `uploads.get_kickoff_field` | 221 | `uploads.check_billing`, `uploads.get_kickoff` |
| `uploads.get_task_field` | 179 | `uploads.check_billing` |
| `uploads.check_session_target` | 296 | `services.is_live_connection`, `uploads.get_kickoff_field`, `uploads.get_task_field` |
| `uploads.issue_upload_capability` | 320 | `services.digest`, `services.is_live_connection`, `uploads.check_session_target` |
| `tasks.import_upload` | 51 | `services.is_live_connection`, `tasks.storage_post`, `uploads.issue_upload_capability` |
| `tasks.prune_expired_state` | 275 | Leaf (ORM/SDK/builtins only) |
| `tasks.publish_notification` | 195 | Leaf (ORM/SDK/builtins only) |
| `tasks_base.CommitAwareTask.apply_async` | 25 | Leaf (ORM/SDK/builtins only) |
| `tasks_base.schedule_task_publication` | 14 | Leaf (ORM/SDK/builtins only) |
| `uploads.UploadConflict.__init__` | 140 | Leaf (ORM/SDK/builtins only) |
| `uploads.get_session` | 255 | Leaf (ORM/SDK/builtins only) |
| `uploads.attach_upload` | 682 | `uploads.check_session_target`, `uploads.get_session` |
| `uploads.authorize_cleanup` | 947 | Leaf (ORM/SDK/builtins only) |
| `uploads.authorize_upload_replay` | 113 | `services.is_live_connection`, `uploads.check_session_target`, `uploads.get_session`, `uploads.get_task_field` |
| `uploads.get_upload_capability` | 409 | `services.digest`, `services.is_live_connection`, `uploads.check_session_target` |
| `uploads.complete_upload` | 561 | `file_metadata.canonical_content_type`, `uploads.check_session_target`, `uploads.get_upload_capability` |
| `uploads.serialize_session` | 345 | `services.is_live_connection` |
| `uploads.create_session` | 376 | `uploads.get_kickoff_field`, `uploads.get_task_field`, `uploads.issue_upload_capability`, `uploads.serialize_session` |
| `uploads.create_upload_token` | 95 | `uploads.get_session`, `uploads.issue_upload_capability` |
| `uploads.get_attachment` | 79 | Leaf (ORM/SDK/builtins only) |
| `uploads.prepare_complete_payload` | 836 | `uploads.check_complete_file_scopes`, `uploads.check_session_target`, `uploads.get_session`, `uploads.require_file_scopes` |
| `uploads.prepare_run_payload` | 723 | `uploads.check_session_target`, `uploads.get_session`, `uploads.require_file_scopes` |
| `uploads.queue_import` | 641 | `uploads.check_session_target`, `uploads.get_session` |
| `uploads.validate_files` | 445 | `file_metadata.encoded_file_id`, `services.get_delegation`, `services.is_live_connection`, `uploads.check_billing`, `uploads.get_upload_capability` |
| `views.AttachmentDetailView.get` | 363 | `uploads.get_attachment` |
| `views.AuthorizationView.get` | 220 | `consent.create_authorization_request` |
| `views.BusinessView.initial` | 322 | `uploads.check_billing` |
| `views.ConnectionRevokeView.delete` | 274 | `services.revoke_connection` |
| `views.ConnectionsView.get` | 268 | `services.list_connections` |
| `views.ConsentView.get` | 173 | `consent.get_context` |
| `views.ConsentView.post` | 180 | `consent.approve_request` |
| `views.DelegationView.post` | 112 | `services.delegate` |
| `views.EnabledMixin.dispatch` | 88 | Leaf (ORM/SDK/builtins only) |
| `views.FileValidationView.post` | 123 | `uploads.validate_files` |
| `views.IntrospectionView.post` | 104 | `services.introspect` |
| `views.KickoffView.get` | 348 | `uploads.get_kickoff` |
| `views.LoginCodeView.post` | 156 | `consent.create_login_code` |
| `views.LoginCompleteView.get` | 190 | `consent.consume_login_code` |
| `views.MCPTokenView.post` | 242 | `oauth.token_connection` |
| `views.RegistrationManagementView.get` | 332 | `oauth.public_registration_response` |
| `views.RegistrationManagementView.put` | 337 | `oauth.public_registration_response`, `oauth.registration_error` |
| `views.RegistrationView.post` | 258 | `oauth.registration_error`, `oauth.save_registered_client` |
| `views.ResourceMetadataView.get` | 280 | Leaf (ORM/SDK/builtins only) |
| `views.ServerMetadataView.get` | 292 | Leaf (ORM/SDK/builtins only) |
| `views.UploadAttachView.authorize_replay` | 445 | `uploads.authorize_upload_replay` |
| `views.UploadAttachView.post` | 452 | `uploads.attach_upload` |
| `views.UploadCleanupView.post` | 139 | `uploads.authorize_cleanup` |
| `views.UploadCompletionView.post` | 131 | `uploads.complete_upload` |
| `views.UploadCreateView.post` | 375 | `uploads.create_session` |
| `views.UploadImportView.authorize_replay` | 419 | `uploads.authorize_upload_replay` |
| `views.UploadImportView.post` | 426 | `uploads.queue_import` |
| `views.UploadStatusView.get` | 396 | `uploads.get_session`, `uploads.serialize_session` |
| `views.UploadStatusView.initial` | 392 | `uploads.check_billing` |
| `views.UploadTokenView.post` | 407 | `uploads.create_upload_token` |

## Mock boundaries and required assertions

| Tested path | Mocked external boundary | Real dependencies / assertions |
|---|---|---|
| Business writes and replay | `publish_notification.delay` publication hint | Real TaskPublication rows; exact hint calls built from ORM before assertion; replay does not create a second row |
| Ordinary fixture construction | Celery base `Task.apply_async` | Only ACL sync for an existing fixture Workflow is allowed; exact args checked, execution context must be absent |
| Analytics | external `analytics.track` | Actual AnalyticService configuration gate disabled; assert_not_called |
| Notification publication | destination task `apply_async` | Real publication row/lock/state/lease/attempts; exact persisted args, kwargs, task_id; future/active lease assert_not_called |
| Import execution | `storage_post`; token randomness at the upload call site | Real session/job/capability rows, live permission/billing; exact path, URL, filename, session ID and credential; queued future/active lease assert_not_called |
| Storage HTTP transport | requests.Session factory and client.post | Real Session context manager, no magic-method mock; explicit URL, service-secret header, body, timeout, no proxies/redirects |
| CIMD | SDK SafeMetadataFetcher.fetch | Real Application/ClientPolicy registration; exact client URL argument |

No ORM manager, related manager, QuerySet, raw SQL, property, save(), super(),
magic method or transaction.atomic is mocked. Fixture constructors are shared
in conftest.py; tests contain no global helper functions or fixture copies.
Core account/user/workflow/template setup uses existing project fixture factories.
Actual fieldset regression setup uses create_test_fieldset_template and the
normal template-to-workflow services; nested fields retain task_id=None.
Standalone TaskField/FieldTemplate constructors remain a narrow fixture
exception: the project has no factory for a standalone file field. Existing
fieldset and kickoff factories create different relationships. The user
authorized documenting that exception instead of inventing a helper or changing
legacy field relationships merely to satisfy a constructor count.
Expected bulk call lists are built before the assertion phase, including fixture
teardown. Every named mock has an argument assertion or assert_not_called.

## Test cases and existing test matrix

Each row is an existing concrete test function. Parametrization expands distinct
inputs into separate pytest cases. `Test=Yes` means the test exists, not a claim
that every production branch is covered. AAA and one-result scenarios apply;
idempotent replay, concurrency, lease fencing and outbox recovery are single
state-transition scenarios with repeated delivery of the same operation.
HTTP setup requests establish preconditions before the act under test.

| Test cases | Annotation | Test | Existing test |
|---|---|---|---|
| `list_attachments`: target filter | target filter -> permissions and pagination; separate inputs: ['task_id', 'workflow_id'] | Yes | `test_attachments.py::test_list_attachments__target_filter__permissions_and_pagination` |
| `list_attachments`: foreign public file | foreign public file -> account isolated | Yes | `test_attachments.py::test_list_attachments__foreign_public_file__account_isolated` |
| `cimd`: https metadata client | https metadata client -> registered without introspection | Yes | `test_cimd.py::test_cimd__https_metadata_client__registered_without_introspection` |
| `cimd`: private metadata url | private metadata url -> deny | Yes | `test_cimd.py::test_cimd__private_metadata_url__deny` |
| `comment`: recipients and broker failure | recipients and broker failure -> durable recoverable outbox | Yes | `test_comment_outbox.py::test_comment__recipients_and_broker_failure__durable_recoverable_outbox` |
| `complete`: fieldset upload reference | fieldset upload reference -> file scope; separate inputs: [True, False] | Yes | `test_complete_uploads.py::test_complete__fieldset_upload_reference__file_scope` |
| `complete`: fieldset file clear | fieldset file clear -> file scope and replay; separate inputs: [FieldType.FILE, FieldType.TEXT]; [True, False] | Yes | `test_complete_uploads.py::test_complete__fieldset_file_clear__file_scope_and_replay` |
| `complete`: cached file clear lower scopes | cached file clear lower scopes -> denied | Yes | `test_complete_uploads.py::test_complete__cached_file_clear_lower_scopes__denied` |
| `complete`: clear existing file | clear existing file -> requires file scope; separate inputs: [True, False]; [None, [], ''] | Yes | `test_complete_uploads.py::test_complete__clear_existing_file__requires_file_scope` |
| `complete`: verified upload reference | verified upload reference -> conditional file scope; separate inputs: [True, False] | Yes | `test_complete_uploads.py::test_complete__verified_upload_reference__conditional_file_scope` |
| `complete`: unverified file input | unverified file input -> 400; separate inputs: [['https://files.test/arbitrary-file'], [{'upload_id': 'invalid-uuid'}]] | Yes | `test_complete_uploads.py::test_complete__unverified_file_input__400` |
| `run`: concurrent identical requests | concurrent identical requests -> one business transaction | Yes | `test_concurrency.py::test_run__concurrent_identical_requests__one_business_transaction` |
| `upload_serializer`: size boundary default target | size boundary default target -> valid; separate inputs: [1, 5] | Yes | `test_file_metadata.py::test_upload_serializer__size_boundary_default_target__valid` |
| `upload_serializer`: oversize | oversize -> message constant | Yes | `test_file_metadata.py::test_upload_serializer__oversize__message_constant` |
| `upload_serializer`: ambiguous target | ambiguous target -> message constant; separate inputs: [{}, {'task_id': 1, 'template_id': 1}] | Yes | `test_file_metadata.py::test_upload_serializer__ambiguous_target__message_constant` |
| `upload_metadata`: same as storage | same as storage -> canonical; separate inputs: [('text/html', 'application/octet-stream'), ('image/svg+xml', 'application/octet-stream'), ('application/unknown', 'application/octet-stream'), ('TEXT/PLAIN', 'text/plain')] | Yes | `test_file_metadata.py::test_upload_metadata__same_as_storage__canonical` |
| `upload_filename`: storage algorithm | storage algorithm -> same canonical; separate inputs: [('my report.pdf', 'my_report.pdf'), ('.hidden.txt', 'hidden.txt'), ('мой отчёт.txt', 'мой_отчёт.txt'), ('report!@#$.txt', 'report_.txt'), ('report.pdf ', 'report.pdf_')] | Yes | `test_file_metadata.py::test_upload_filename__storage_algorithm__same_canonical` |
| `import`: concurrent account workers | concurrent account workers -> two active third deferred | Yes | `test_import_concurrency.py::test_import__concurrent_account_workers__two_active_third_deferred` |
| `get_kickoff_field`: unavailable fieldset parent | unavailable fieldset parent -> not found; separate inputs: ['hidden', 'field_deleted', 'fieldset_deleted', 'kickoff_deleted'] | Yes | `test_kickoff_uploads.py::test_get_kickoff_field__unavailable_fieldset_parent__not_found` |
| `run`: verified kickoff session | verified kickoff session -> consumed transactionally; separate inputs: [True, False]; ['direct', 'fieldset'] | Yes | `test_kickoff_uploads.py::test_run__verified_kickoff_session__consumed_transactionally` |
| `import`: stale completion | stale completion -> preserves newer claim; separate inputs: [True, False] | Yes | `test_lease_fencing.py::test_import__stale_completion__preserves_newer_claim` |
| `publication`: stale completion | stale completion -> preserves newer claim; separate inputs: [True, False] | Yes | `test_lease_fencing.py::test_publication__stale_completion__preserves_newer_claim` |
| `delegate`: long unicode encoded path | long unicode encoded path -> http and db accept | Yes | `test_legacy_files.py::test_delegate__long_unicode_encoded_path__http_and_db_accept` |
| `validate_files`: legacy encoded identity | legacy encoded identity -> metadata and ticket; separate inputs: ['NiihssB_Drawing (v2).odg', 'legacy_мой отчёт (версия2).pdf', '😀' * 508 + '.pdf'] | Yes | `test_legacy_files.py::test_validate_files__legacy_encoded_identity__metadata_and_ticket` |
| `delegate`: noncanonical or unsafe file path | noncanonical or unsafe file path -> denied; separate inputs: ['raw space.txt', '%2F', '%5C', '%252F', '%3F', '%23', '%00', '..', 'bad%ff', 'legacy%20name%2etxt'] | Yes | `test_legacy_files.py::test_delegate__noncanonical_or_unsafe_file_path__denied` |
| `file_validation`: unsafe raw identity | unsafe raw identity -> 400; separate inputs: ['a/b', 'a\\b', 'a?b', 'a#b', '%2f', '..'] | Yes | `test_legacy_files.py::test_file_validation__unsafe_raw_identity__400` |
| `oauth_revoke`: bound token | bound token -> revokes connection; separate inputs: [('access_token', False), ('access_token', True), ('refresh_token', False)] | Yes | `test_oauth_endpoints.py::test_oauth_revoke__bound_token__revokes_connection` |
| `oauth_revoke`: foreign client | foreign client -> preserves grant; separate inputs: ['access_token', 'refresh_token'] | Yes | `test_oauth_endpoints.py::test_oauth_revoke__foreign_client__preserves_grant` |
| `oauth_revoke`: unknown token | unknown token -> successful noop | Yes | `test_oauth_endpoints.py::test_oauth_revoke__unknown_token__successful_noop` |
| `oauth_revoke`: disabled client | disabled client -> protocol denial | Yes | `test_oauth_endpoints.py::test_oauth_revoke__disabled_client__protocol_denial` |
| `resource_metadata`: public alias | public alias -> exact contract; separate inputs: ['/.well-known/oauth-protected-resource', '/.well-known/oauth-protected-resource/mcp'] | Yes | `test_oauth_endpoints.py::test_resource_metadata__public_alias__exact_contract` |
| `server_metadata`: public endpoint | public endpoint -> exact contract | Yes | `test_oauth_endpoints.py::test_server_metadata__public_endpoint__exact_contract` |
| `metadata`: disabled mcp | disabled mcp -> not found; separate inputs: ['/.well-known/oauth-protected-resource', '/.well-known/oauth-protected-resource/mcp', '/.well-known/oauth-authorization-server'] | Yes | `test_oauth_endpoints.py::test_metadata__disabled_mcp__not_found` |
| `registration`: csrf enforced public origin | csrf enforced public origin -> valid | Yes | `test_oauth_endpoints.py::test_registration__csrf_enforced_public_origin__valid` |
| `registration_management`: authorized operation | authorized operation -> expected status; separate inputs: [('read', 200), ('update', 200), ('invalid', 400), ('delete', 204)] | Yes | `test_oauth_endpoints.py::test_registration_management__authorized_operation__expected_status` |
| `registration`: malformed metadata | malformed metadata -> 400; separate inputs: [('grant_types', None), ('grant_types', [{}]), ('response_types', None), ('token_endpoint_auth_method', {}), ('client_name', [])] | Yes | `test_oauth_endpoints.py::test_registration__malformed_metadata__400` |
| `protocol_posts`: csrf enforced | csrf enforced -> oauth error; separate inputs: [('token', 400, 'invalid_grant'), ('revoke', 401, 'invalid_client')] | Yes | `test_oauth_endpoints.py::test_protocol_posts__csrf_enforced__oauth_error` |
| `disabled_client`: private introspection | private introspection -> inactive | Yes | `test_oauth_endpoints.py::test_disabled_client__private_introspection__inactive` |
| `introspection`: full middleware | full middleware -> positive identity | Yes | `test_oauth_endpoints.py::test_introspection__full_middleware__positive_identity` |
| `delegation`: full middleware | full middleware -> no browser capability cookie | Yes | `test_oauth_endpoints.py::test_delegation__full_middleware__no_browser_capability_cookie` |
| `prune`: expired ephemeral records | expired ephemeral records -> keep live and pending | Yes | `test_pruning.py::test_prune__expired_ephemeral_records__keep_live_and_pending` |
| `prune`: bounded expired batch | bounded expired batch -> preserves remaining and live | Yes | `test_pruning.py::test_prune__bounded_expired_batch__preserves_remaining_and_live` |
| `redaction`: oauth request celery vars and spans | oauth request celery vars and spans -> no secrets | Yes | `test_redaction.py::test_redaction__oauth_request_celery_vars_and_spans__no_secrets` |
| `redaction`: ordinary event | ordinary event -> preserves diagnostics | Yes | `test_redaction.py::test_redaction__ordinary_event__preserves_diagnostics` |
| `redaction`: private header without url | private header without url -> strips frame secrets | Yes | `test_redaction.py::test_redaction__private_header_without_url__strips_frame_secrets` |
| `refresh`: rotation or reuse | rotation or reuse -> expected connection state; separate inputs: [(False, 200), (True, 400)] | Yes | `test_refresh.py::test_refresh__rotation_or_reuse__expected_connection_state` |
| `refresh`: disabled client | disabled client -> deny | Yes | `test_refresh.py::test_refresh__disabled_client__deny` |
| `schema`: mcp public security and private routes | mcp public security and private routes -> exact | Yes | `test_schema.py::test_schema__mcp_public_security_and_private_routes__exact` |
| `list_connections`: mixed owners | mixed owners -> stable scoped order; separate inputs: [False, True] | Yes | `test_services.py::test_list_connections__mixed_owners__stable_scoped_order` |
| `list_connections`: other user | other user -> empty | Yes | `test_services.py::test_list_connections__other_user__empty` |
| `introspect`: active grant | active grant -> bound identity | Yes | `test_services.py::test_introspect__active_grant__bound_identity` |
| `introspect`: changed identity | changed identity -> inactive; separate inputs: ['disabled', 'status', 'tenant', 'expiry', 'client'] | Yes | `test_services.py::test_introspect__changed_identity__inactive` |
| `delegate`: unlisted route | unlisted route -> denied | Yes | `test_services.py::test_delegate__unlisted_route__denied` |
| `delegate`: source shorter than 60s | source shorter than 60s -> bounded hashed | Yes | `test_services.py::test_delegate__source_shorter_than_60s__bounded_hashed` |
| `revoke_connection`: delegated token | delegated token -> immediate denial | Yes | `test_services.py::test_revoke_connection__delegated_token__immediate_denial` |
| `delegate`: attach without both writes | attach without both writes -> denied | Yes | `test_services.py::test_delegate__attach_without_both_writes__denied` |
| `consent`: step up upload connection | step up upload connection -> same identity strict tokens | Yes | `test_step_up.py::test_consent__step_up_upload_connection__same_identity_strict_tokens` |
| `dispatch_pending_imports`: job schedule | job schedule -> only due; separate inputs: ['due', 'future', 'expired_lease', 'live_lease', 'done', 'failed'] | Yes | `test_tasks.py::test_dispatch_pending_imports__job_schedule__only_due` |
| `dispatch_pending_imports`: disabled | disabled -> no delivery | Yes | `test_tasks.py::test_dispatch_pending_imports__disabled__no_delivery` |
| `dispatch_pending_imports`: empty queue | empty queue -> no delivery | Yes | `test_tasks.py::test_dispatch_pending_imports__empty_queue__no_delivery` |
| `cleanup_uploads`: feature gate | feature gate -> bounded request; separate inputs: [False, True] | Yes | `test_tasks.py::test_cleanup_uploads__feature_gate__bounded_request` |
| `import_upload`: retry schedule and lease | retry schedule and lease -> respects claim; separate inputs: ['future', 'due', 'lease', 'expired_lease'] | Yes | `test_tasks.py::test_import_upload__retry_schedule_and_lease__respects_claim` |
| `publish_notification`: retry schedule and lease | retry schedule and lease -> respects claim; separate inputs: ['future', 'due', 'lease', 'expired_lease'] | Yes | `test_tasks.py::test_publish_notification__retry_schedule_and_lease__respects_claim` |
| `storage_post`: private service | private service -> no proxy or redirect; separate inputs: [200, 302] | Yes | `test_tasks.py::test_storage_post__private_service__no_proxy_or_redirect` |
| `notification`: business transaction rollback | business transaction rollback -> no publication | Yes | `test_tasks.py::test_notification__business_transaction_rollback__no_publication` |
| `notification`: broker failure | broker failure -> persist and recover | Yes | `test_tasks.py::test_notification__broker_failure__persist_and_recover` |
| `notification`: successful publish retry | successful publish retry -> one send | Yes | `test_tasks.py::test_notification__successful_publish_retry__one_send` |
| `create_session`: template task fieldset | template task fieldset -> real parent link | Yes | `test_uploads.py::test_create_session__template_task_fieldset__real_parent_link` |
| `get_task_field`: unavailable fieldset parent | unavailable fieldset parent -> not found; separate inputs: ['hidden', 'field_deleted', 'fieldset_deleted', 'task_deleted', 'workflow_deleted', 'missing_parent', 'foreign_parent'] | Yes | `test_uploads.py::test_get_task_field__unavailable_fieldset_parent__not_found` |
| `attach_upload`: task fieldset | task fieldset -> single real attachment | Yes | `test_uploads.py::test_attach_upload__task_fieldset__single_real_attachment` |
| `attach_upload`: fieldset replay | fieldset replay -> current visibility; separate inputs: ['visible', 'hidden', 'parent_deleted'] | Yes | `test_uploads.py::test_attach_upload__fieldset_replay__current_visibility` |
| `queue_import`: invalid url port | invalid url port -> standard validation error | Yes | `test_uploads.py::test_queue_import__invalid_url_port__standard_validation_error` |
| `create_upload_token`: session near expiry | session near expiry -> bounded lifetime | Yes | `test_uploads.py::test_create_upload_token__session_near_expiry__bounded_lifetime` |
| `upload`: hidden target | hidden target -> callback denied; separate inputs: [('validate-files', 200), ('complete-upload', 403)] | Yes | `test_uploads.py::test_upload__hidden_target__callback_denied` |
| `validate_files`: ticket authorization | ticket authorization -> expected activity; separate inputs: [('valid', True), ('expired', False), ('missing', False)] | Yes | `test_uploads.py::test_validate_files__ticket_authorization__expected_activity` |
| `attach_upload`: three files | three files -> preserves all links | Yes | `test_uploads.py::test_attach_upload__three_files__preserves_all_links` |
| `subscription_expired`: file access or revocation | file access or revocation -> expected status; separate inputs: [('validate', 200), ('revoke', 204)] | Yes | `test_uploads.py::test_subscription_expired__file_access_or_revocation__expected_status` |
| `cleanup`: deleted attachment reference | deleted attachment reference -> conservative deny | Yes | `test_uploads.py::test_cleanup__deleted_attachment_reference__conservative_deny` |
| `cleanup`: lost completion callback | lost completion callback -> deterministic file only | Yes | `test_uploads.py::test_cleanup__lost_completion_callback__deterministic_file_only` |
| `upload`: spaced filename callback | spaced filename callback -> canonical ready; separate inputs: ['upload', 'import'] | Yes | `test_uploads.py::test_upload__spaced_filename_callback__canonical_ready` |
| `consent_context`: live request | live request -> bound identity; separate inputs: [False, True] | Yes | `test_views.py::test_consent_context__live_request__bound_identity` |
| `consent_context`: unavailable request | unavailable request -> denied; separate inputs: [('missing', 404, messages.MSG_MCP_0019), ('foreign_user', 404, messages.MSG_MCP_0019), ('foreign_account', 404, messages.MSG_MCP_0019), ('expired', 410, messages.MSG_MCP_0021), ('consumed', 410, messages.MSG_MCP_0021)] | Yes | `test_views.py::test_consent_context__unavailable_request__denied` |
| `consent_context`: invalid query | invalid query -> standard error; separate inputs: [({}, 'This field is required.'), ({'request_id': ''}, 'Must be a valid UUID.'), ({'request_id': 'undefined'}, 'Must be a valid UUID.'), ({'request_id': 123}, 'Must be a valid UUID.')] | Yes | `test_views.py::test_consent_context__invalid_query__standard_error` |
| `browser_mcp`: anonymous | anonymous -> requires login; separate inputs: ['/integrations/mcp/consent', '/integrations/mcp/connections'] | Yes | `test_views.py::test_browser_mcp__anonymous__requires_login` |
| `browser_mcp`: api key | api key -> requires user login; separate inputs: ['/integrations/mcp/consent', '/integrations/mcp/connections'] | Yes | `test_views.py::test_browser_mcp__api_key__requires_user_login` |
| `connections`: user login | user login -> scoped response; separate inputs: [False, True] | Yes | `test_views.py::test_connections__user_login__scoped_response` |
| `mcp_request`: null field | null field -> standard validation error; separate inputs: [('/internal/mcp/introspect', 'resource'), ('/internal/mcp/delegate', 'tool'), ('/internal/mcp/validate-files', 'file_id'), ('/internal/mcp/complete-upload', 'upload_session_id'), ('/internal/mcp/cleanup-upload', 'upload_session_id'), ('/integrations/mcp/login-code', 'request_id'), ('/integrations/mcp/consent', 'request_id'), ('/integrations/mcp/uploads', 'size')] | Yes | `test_views.py::test_mcp_request__null_field__standard_validation_error` |
| `run`: invalid idempotency key | invalid idempotency key -> standard validation error; separate inputs: [None, '', 'x' * 129, 'has space', 'é'] | Yes | `test_views.py::test_run__invalid_idempotency_key__standard_validation_error` |
| `introspection`: invalid token | invalid token -> standard validation error; separate inputs: [(None, 'This field may not be null.'), ('', 'This field may not be blank.'), ({}, 'Not a valid string.')] | Yes | `test_views.py::test_introspection__invalid_token__standard_validation_error` |
| `service_auth`: non ascii header | non ascii header -> 401; separate inputs: [('HTTP_X_MCP_SERVICE_SECRET', '/internal/mcp/introspect'), ('HTTP_X_MCP_FILE_SERVICE_SECRET', '/internal/mcp/validate-files'), ('HTTP_AUTHORIZATION', '/internal/mcp/validate-files')] | Yes | `test_views.py::test_service_auth__non_ascii_header__401` |
| `delegate`: invalid credentials | invalid credentials -> distinct code; separate inputs: [(False, 'service_auth_failed'), (True, 'invalid_token')] | Yes | `test_views.py::test_delegate__invalid_credentials__distinct_code` |
| `run`: legacy connection alias | legacy connection alias -> replay and group revocation | Yes | `test_views.py::test_run__legacy_connection_alias__replay_and_group_revocation` |
| `ordinary_login`: file cookie | file cookie -> unchanged | Yes | `test_views.py::test_ordinary_login__file_cookie__unchanged` |
| `comment`: plain text same key | plain text same key -> successful replay | Yes | `test_views.py::test_comment__plain_text_same_key__successful_replay` |
| `introspection`: user token not service | user token not service -> 401 | Yes | `test_views.py::test_introspection__user_token_not_service__401` |
| `delegation`: different route and method | different route and method -> default deny; separate inputs: [('GET', '/accounts/user'), ('POST', '/templates')] | Yes | `test_views.py::test_delegation__different_route_and_method__default_deny` |
| `delegation`: public custom auth endpoint | public custom auth endpoint -> denied | Yes | `test_views.py::test_delegation__public_custom_auth_endpoint__denied` |
| `run`: same key same payload | same key same payload -> one workflow | Yes | `test_views.py::test_run__same_key_same_payload__one_workflow` |
| `run`: same key different payload | same key different payload -> 409 | Yes | `test_views.py::test_run__same_key_different_payload__409` |
| `complete`: after run same key replay | after run same key replay -> same success | Yes | `test_views.py::test_complete__after_run_same_key_replay__same_success` |
| `oauth`: bridge consent code pkce | bridge consent code pkce -> bound connection | Yes | `test_views.py::test_oauth__bridge_consent_code_pkce__bound_connection` |
| `complete`: remove existing text file link | remove existing text file link -> requires write; separate inputs: [FieldType.TEXT, FieldType.STRING, FieldType.URL]; [True, False] | Yes | `test_write_file_links.py::test_complete__remove_existing_text_file_link__requires_write` |
| `write`: text file link | text file link -> current scope and permission; separate inputs: ['run_workflow', 'complete_task']; ['foreign', 'restricted', 'scope', 'allowed'] | Yes | `test_write_file_links.py::test_write__text_file_link__current_scope_and_permission` |

## Defaults, edge cases and protocol annotations

| Function/path | Test cases | Annotation | Test |
|---|---|---|---|
| UploadSerializer | canonical MIME/filename; target ID/type consistency; size boundary and invalid required fields | Framework CharField/UUID/Integer validators retain native messages, custom mixins produce message/code/details | Yes: metadata, upload and HTTP validation tests |
| Internal/user business serializers | null; blank; invalid object token; required identity fields | Internal FileValidation is a normal business serializer; it uses both AdditionalValidationMixin and CustomValidationErrorMixin | Yes: test_mcp_request__null_field and test_introspection__invalid_token |
| Delegation and file paths | unsafe delimiters, null byte, noncanonical percent encoding, long Unicode segment | Path must be the canonical encoded single segment; old file identities remain usable | Yes: test_legacy_files |
| Idempotency | omitted/blank/non-ASCII/space/overlong key; same payload; changed payload; lower replay scopes | 400/409 business response uses message/code/details, details={} allowed for non-field validation | Yes: test_views, completion and write-file tests |
| queue_import | malformed URL port | Service validation never exposes raw ValueError; no job/session mutation or task dispatch | Yes: test_queue_import__invalid_url_port |
| create_upload_token | session expires sooner than 300 seconds | expires_in is bounded by the actual persisted capability/session expiry | Yes: test_create_upload_token__session_near_expiry |
| import_upload / publish_notification | queued future, queued due, live lease, expired lease | Guards run after row lock; future delivery does not consume attempts or call external components; expired running lease remains recoverable | Yes: test_tasks schedule/lease cases |
| OAuth authorize/token/revoke/DCR | invalid resource/grant/client/metadata; PKCE; rotation/reuse; registration management | Standard OAuth error/status/redirect formats deliberately differ from business message/code/details; do not run through DRF business serializers | Yes: OAuth, refresh, CIMD and full HTTP lifecycle tests |
| SDK method overrides and callback payloads | DOT positional callback forwarding and existing Celery positional args | Preserve the external SDK signatures and durable legacy task args; application service calls use named arguments. Builtin positional-only operations remain positional | Protocol compatibility annotation |
| Shared fixtures | account before users; project fixture factories; real MCP protocol-state constructors | Conftest fixtures are pytest infrastructure; the ban on global test helpers does not ban shared conftest fixtures | Structural audit |
| MCP persistence | short-lived grants/codes/capabilities/outbox and revoked_at connection | Temporary protocol state is physically pruned; persistent business models retain their existing soft-delete behavior. Applied migrations are preserved | ORM pruning and revocation tests |
| Task fieldsets | real template -> workflow; upload create; hidden/deleted field, deleted/missing/foreign parent; attach and replay | TaskField.task_id remains None. Resolve both task and fieldset.task; recheck current field/parent visibility on replay | Yes: test_uploads fieldset cases |
| Complete fieldsets | verified references; FILE/TEXT clearing; reduced scopes on initial write and replay | Scope and reference mapping includes fieldset-only fields; real TaskFieldService creates one workflow-scope attachment with real ACL | Yes: test_complete_uploads fieldset cases |
| Kickoff fieldsets | direct/fieldset target; valid upload reference; missing file scope; hidden/deleted field/fieldset/kickoff | Resolve kickoff through fieldset without assigning kickoff_id to the nested field | Yes: test_kickoff_uploads |
| Message localization | custom serializer errors, import validation, conflicts and idempotency errors | Canonical MSG_MCP constants use gettext_lazy; tests assert the constants. Framework and protocol-owned messages retain their existing owners | Yes: test_file_metadata, test_legacy_files, test_uploads, test_views |

## Local translation registry

`src/mcp/messages.py` is the canonical source for public MCP business messages.
The MSG_MCP namespace was checked against the current repository before adding
these identifiers. This registry replaces the unspecified external translation
table for this local review; no external document was written. English source
strings are ready for normal gettext catalog extraction. This review does not
claim that new translated catalogs have been published.

| Identifier | English source message | Owning behavior |
|---|---|---|
| MSG_MCP_0001 | File exceeds the size limit. | Upload size validation |
| MSG_MCP_0002 | Specify exactly the target ID. | Upload target validation |
| MSG_MCP_0003 | Unsafe file identifier. | File identity validation |
| MSG_MCP_0004 | File field API name is ambiguous in this task. | Task field resolution |
| MSG_MCP_0005 | Upload session ID must be a UUID. | Session lookup |
| MSG_MCP_0006 | Unknown upload session. | Session access |
| MSG_MCP_0007 | Upload session is unavailable. | Upload capability issuance |
| MSG_MCP_0008 | Conflicting upload completion. | Completion conflict |
| MSG_MCP_0009 | Upload is already consumed. | Completion conflict |
| MSG_MCP_0010 | Upload metadata does not match the session. | Completion metadata validation |
| MSG_MCP_0011 | Imports require an HTTPS URL on port 443. | Import URL validation |
| MSG_MCP_0012 | Session cannot accept an import. | Import state conflict |
| MSG_MCP_0013 | Verified completed upload is required. | Attachment state conflict |
| MSG_MCP_0014 | File service is not configured. | File service availability |
| MSG_MCP_0015 | Use upload-session file references. | Run/complete reference validation |
| MSG_MCP_0016 | Use {upload_id:UUID} file references. | Run/complete reference shape |
| MSG_MCP_0017 | Require Idempotency-Key: 1-128 ASCII chars. | Idempotency key validation |
| MSG_MCP_0018 | Idempotency key conflict. | Idempotency payload conflict |
| MSG_MCP_0019 | Unknown authorization request. | Browser consent lookup |
| MSG_MCP_0020 | Import is no longer authorized. | Persisted import failure |
| MSG_MCP_0021 | Authorization request expired or consumed. | Browser consent expiry |

OAuth errors are a distinct protocol boundary: DOT/oauthlib own error codes,
HTTP statuses and redirects. Those responses deliberately retain the OAuth
format. Internal credential/header identifiers and native framework validation
messages are not copied into the business translation registry. Scope-denial
responses retain machine-readable code/required_scopes needed by MCP clients,
with the normal project PermissionDenied text.

## OAuth throttle API and runbook

On 2026-10-13 the separate Redis Lua rate guard was replaced by the existing
backend `CustomSimpleRateThrottle`. `OAuthThrottleMiddleware` only selects
one of three scope subclasses and formats OAuth 429/503 responses. Rates use
`THROTTLE_14` (`10/min`, registration), `THROTTLE_15` (`60/min`, shared
GET/HEAD authorize/login), and `THROTTLE_16` (`120/min`, shared POST token/revoke).
These are minimum request intervals, using the default backend cache and DRF
IP identity. No separate Redis alias, Lua counter or proxy flags remain.
See `docs/mcp-runbook.md` for configuration. The removed guard's historical
validation evidence below does not describe the current throttle's semantics.

## Existing backend throttle validation - 2026-10-13

- Targeted OAuth/startup/shared-throttle tests: 79 passed, 6 warnings.
- Full backend MCP suite: 265 passed, 4 warnings.
- Real Django/MCP HTTP lifecycle: 1 passed, 6 warnings. This lifecycle test
  disables timing limits; refusal/interval/state preservation are verified by
  the backend OAuth tests.
- Two adapter instances share the actual default Redis-cache interval: passed.
- Changed Python lint/format, diff whitespace and both Compose configurations:
  passed. Runtime Redis Lua atomic-admission tests were removed with that guard.

JUnit results: `.mcp-validation/oauth-existing-throttle-20261013/`.
All validation is local with disposable PostgreSQL/Redis and test credentials;
no production configuration was changed or deployment performed.

## Authentication ownership - 2026-10-13

- `authentication/services/mcp_auth.py`: login, private service/storage and
  delegation authentication; DRF settings point to the relocated classes.
- `authentication/services/mcp_oauth.py`: OAuth SDK validator.
- `authentication/services/oauth.py`, `consent.py`, `delegation.py`: token
  exchange/client registration, browser consent and restricted credentials.
- `authentication/views/`: OAuth, consent, introspection and delegation views.
  `authentication/oauth_urls.py` retains the existing OAuth namespace and paths.
- OAuth, consent and delegation serializers join `authentication/serializers.py`;
  OpenAPI authentication schemes register from `AuthConfig.ready()`.
- `authentication/middleware.py` selects the common OAuth throttles and validates
  delegated requests. `mcp/middleware.py` only owns MCP execution context and
  idempotency, including authorization rechecks after acquiring the write lock.

Connection/credential persistence remains in the `mcp` Django application.
The relocation does not rename tables, move model labels or add migrations.
Public/internal URLs and storage callbacks remain unchanged. Historical function
inventory and full-suite records below refer to their original module locations.

Final validation after all serializer moves: 672 passed, 4 warnings in 129.18s
(265 MCP and 407 existing authentication tests). Real Django/MCP HTTP lifecycle:
1 passed, 4 warnings in 8.16s. Django check has no issues; migration drift check
reports no changes in `authentication` or `mcp`. Changed-source Ruff and diff
whitespace checks pass. The relocated service/view/route bodies and serializer
class definitions match their pre-move ASTs apart from imports.

The first validation was invalid because HTTP and unit/integration suites shared
one test database concurrently (665 passed, 6 failed, 1 error). The clean rerun
passed all 672 cases; final HTTP and suite runs use different test databases.
JUnit receipts and source snapshots are in
`.mcp-validation/auth-relocation-20261013/`. No production deployment occurred.

## Confirmed findings closed

1. Thin views: move login-code consumption, authorization-request creation,
   connection queries, client policy registration, file/kickoff access and
   upload token/import/attach/replay checks into existing services.
2. Serializer errors: all MCP business serializers use the project mixins;
   upload business errors and idempotency 400/409 use the standard envelope.
3. Retry timing: a queued future job/publication cannot burn attempts on an
   early duplicate delivery; expired active claims still recover.
4. Input/time/race defects: malformed import port returns a validation error;
   upload credential lifetime is bounded; a removed token binding/connection
   returns invalid_grant rather than DoesNotExist.
5. Test purity: publication SQL stays real, broker delivery/HTTP/analytics are
   isolated; exact side-effect arguments are asserted. No manager or atomic mock.
6. Remove unused get_connection and constructor-only session_request; avoid
   new pass-through modules. Type MCP arguments, retain 79-column whitespace,
   preserve strict root hooks and shared worktree changes.
7. Fieldset paths: resolve real task/kickoff parent relationships, enforce live
   parent checks, map nested file upload references and require file scope when
   clearing existing links. Attach/replay preserves legacy FK and ACL semantics.
8. Message literals: consolidate business errors into canonical gettext MSG_MCP
   constants and the local registry above. ImportJob/TaskPublication repeated
   states use enums inside the existing models; their persisted fields and
   applied migrations are unchanged.
9. Final style review: internal middleware calls, recursive payload/redaction
   transformations and DRF permission invocation use named arguments. SDK
   override forwarding keeps its required signature; there is no behavior change.
10. Measured local gaps: add 43 scenarios in existing test files for consent
    context, connection lists, SDK revoke, import dispatch/cleanup and metadata.
    These additions use real ORM and exact external-effect assertions. At that
    test-only phase no runtime defect was found; the later guard changed the
    production source and required the new complete run recorded below.

11. Public OAuth resource abuse: add an early shared atomic Redis guard for
    registration, authorization/login and token/revoke; include HEAD and slash
    variants, trusted IP resolution, bounded counters/TTL and native 429/503.
    No SDK hash, AuthorizationRequest write, LoginCode consume or token/grant
    mutation occurs when refused. Keep the ordinary DCR/PKCE/refresh contract.
12. Disabled no-Redis bootstrap: use a safe DummyCache placeholder for cache
    initialization/close/override; an unsupported runtime alias fails closed
    with a sanitized OAuth 503.

## Validation evidence

Validation uses own container `review-mcp-backend-20261009`, runtime snapshot
`pneu-review-mcp-runtime:20261009` (Python 3.12.15, Celery 5.6.3, DOT 3.4.1),
PostgreSQL `test_review_mcp_backend_20261009`, Redis DB 9/10/11/12/13.
Testing retains LocMem auth/session caches; OAuth rate tests use actual Redis
with random per-test review_mcp_ key prefixes. No Redis flush or shared
container deletion occurs. A disabled deployment without a Redis URL uses a
DummyCache placeholder, which safely supports cacheclose and CACHES overrides.
A non-Redis runtime alias produces native OAuth 503 before SDK work.
Backend startup configuration validation was removed on 2026-10-12;
configuration is checked during production setup. Historical test results below
include the configuration tests that were subsequently removed.
The runtime snapshot reuses the completed synthetic helper's installed SDKs;
the older base image itself does not include DOT.

Final full validation runs from a Linux filesystem copy at
`/tmp/review_mcp_snapshot/backend`: all `src` files, including every fixture,
actual staticfiles and the test/configuration entrypoints were copied. The
manifest contains 2910 files. Original source before copy, original source
after copy and Linux snapshot all have the same SHA-256 manifest digest:
`d6e8a690bd44cf6e157c224984e5cf310c1f9739a2df5e575114875562b9d3bf`.
The first completed run retained that digest for both original and snapshot
after tests. It returned 7279 passed and 3 failed in 424.87 seconds; all 202 MCP
cases passed. Two admin failures were validation asset setup: the host's ignored
static manifest lacked Django 5.2 admin/css/dark_mode.css. Real collectstatic
--noinput inside the own Linux snapshot copied 135 files and post-processed
1045 files. Host assets/source were not changed. The third failure was a legacy
test assumption: RelatedApiNameListField reads a ManyToMany relation whose
FieldTemplate ordering is -order, but both test records have the same order.
No tie ordering is guaranteed. Only that assertion now compares sorted lists,
preserving cardinality and membership without changing the production contract.

After this one test correction, the final original/snapshot code, configuration
and fixture manifest contains 1788 files with the same SHA-256 digest:
`f8d47eb6b2abc8a96130136e59270a24cd31e7bb84ebef310628e4b97972c960`.
This digest includes the final named-argument correction in middleware.py,
uploads.py and redaction.py. The earlier named-argument review interrupted only
the own unfinished full coordinator at 5321 passed, 0 failed, 299.54 seconds;
that run is intermediate evidence rather than a final full-suite result.
Generated Linux static assets are recorded separately: 2028 files, digest
`3aff14ffef02cf3fabb2494663d8823c7d074d473b589968c109e408013549ae`.
Post-run equality of source/snapshot code and generated assets was verified with
the same respective digests after full PASS. WhiteNoise and strict manifest
storage remain enabled and
STATIC_ROOT resolves to the real Linux staticfiles. No middleware, fixture,
test scope or installed dependency was removed. All backend application tests
are under `src`; fixed PYTHONHASHSEED=0 is retained rather than selecting a seed
to satisfy the old ordering assumption.

Four pytest-xdist workers use separate Django database clones with the prefix
`test_review_mcp_backend_20261009`. PYTHONHASHSEED=0 makes legacy set-based
parametrization ordering identical across workers. An initial parallel run
stopped at collection because worker hash seeds differed; it is not a test
failure or a successful full-suite result. The slower mounted-source serial
run was interrupted at 596 passed and is also intermediate evidence only.

Final focused command:

```text
docker exec review-mcp-backend-20261009 python -m pytest
  src/mcp/tests/test_file_metadata.py src/mcp/tests/test_legacy_files.py
  src/mcp/tests/test_tasks.py src/mcp/tests/test_complete_uploads.py
  src/mcp/tests/test_kickoff_uploads.py -q --reuse-db
  --basetemp=/tmp/review_mcp_focused_final
```

Result: 72 passed, 4 warnings, 56.05 seconds; exit 0. After collectstatic and the
single legacy assertion correction, the three failed scenarios passed together:
3 passed, 12 warnings, 2.41 seconds; exit 0. Earlier MCP passes and the red
fieldset reproduction are intermediate evidence, not the final full backend
result. The final full-suite command/result is recorded below.

Final named-argument regression command on the Linux snapshot:

```text
python -m pytest src/mcp/tests/test_views.py src/mcp/tests/test_redaction.py
  src/mcp/tests/test_complete_uploads.py src/mcp/tests/test_kickoff_uploads.py
  -q -o 'addopts=--dc=Testing --no-cov --disable-warnings' --reuse-db
  --basetemp=/tmp/review_mcp_named_args_final
```

Result: 60 passed, 4 warnings, 24.76 seconds; exit 0. Ruff and container
pycodestyle (79 columns) pass for the three final changed production files.
The structural AST audit includes local/application named calls, annotations,
no -> None, global-helper prohibition and assertion/mocking restrictions:
Final audit after the new test cases: 277 functions, 122 test functions, 0 issues.

Historical baseline full-suite command (7282 cases, no deselection):

```text
docker exec -w /tmp/review_mcp_snapshot/backend -e PYTHONHASHSEED=0
  review-mcp-backend-20261009 python -m pytest src -q -n 4 --dist=loadfile
  -o 'addopts=--dc=Testing --disable-warnings' --reuse-db
  --basetemp=/tmp/review_mcp_linux_full_source_final --cov=src.mcp --cov-branch
  --cov-report=json:/tmp/review_mcp_coverage_final.json
  --junitxml=/tmp/review_mcp_linux_full_final.xml
```

Result: 7282 passed, 56 warnings, 387.15 seconds; exit 0. JUnit independently
confirms 7282 cases, 202 MCP cases and zero failures/errors. Host log:
`backend/.pytest_cache/review_mcp_linux_full_source_final.log`.

After this baseline PASS, 43 test-only local scenarios were added to conftest,
test_views, test_services, test_tasks and test_oauth_endpoints. At that phase,
all 245 unique MCP cases had
a passing latest result across these recorded runs; this is not claimed as one
single 245-pass invocation:

| Command/scope | Result | Evidence |
|---|---|---|
| Full `src/mcp/tests -q -n 4 --dist=loadfile`, same runtime, branch coverage | 240 passed, 1 failed, 20 warnings, 32.70s; the failure was fixture setup before endpoint execution: duplicate default owner email | review_mcp_paths_final.log / review_mcp_paths_initial.xml |
| Only `test_consent_context__unavailable_request__denied[foreign_account-404-message2]`, after a unique fixture email | 1 passed, 4 warnings, 4.62s; exit 0 | review_mcp_foreign_context_final.log / .xml |
| Only `test_consent_context__invalid_query__standard_error`, four new required/empty/undefined/type scenarios | 4 passed, 4 warnings, 5.41s; exit 0 | review_mcp_context_query_final.log / .xml |

The two focused reruns use --cov-append; production source remains identical.
`backend/.pytest_cache/review_mcp_paths_verified.json` reconciles case identities
from the three XML files: 245 unique cases, zero latest failed cases. It does
not replace or alter the original XML/log evidence.

The historical source/snapshot test manifest before/after targeted validation is
`239ed6f5be14df05a53391f1bb047105b3dae9eff389dd128029c4163f11b497`.
Runtime/configuration manifest excluding test directories is identical between
the full PASS and the final target:
`761f9e5acd320a5f16a875d8df6210e3b05bf4f58dfa041070cb32cb6a5fb0ed`.
Proofs are saved as review_mcp_code_full_proof.json and
review_mcp_targets_proof.json in backend/.pytest_cache. Actual static assets
remain the real collectstatic output; runtime/fixture/middleware scope is intact.

Coverage is a measured limit, not a claim that every defensive branch is tested.
The baseline full run executed 1439/1595 production MCP statements (90.2%) and 314/428
branches (73.4%). After closing the local gaps, measured production coverage was
1470/1595 statements (92.16%) and 329/428 branches (76.87%), excluding tests and
migrations from the denominator. The raw --cov=src.mcp aggregate includes
test/migration files and
must not be used as the production percentage. Parent actual HTTP acceptance
adds real coverage of kickoff/attachment views, get_attachment and upload-token
HTTP serialization; it is separate from this pytest coverage report.

| Function/path | Test case annotation | Test |
|---|---|---|
| consent.get_context / ConsentView.get | Unbound request identity binding; completed login context; missing/foreign/expired/consumed request; exact 400 query errors; anonymous/API-key denial | Yes: test_views context/browser cases |
| services.list_connections / ConnectionsView.get | Owner/account isolation; creation-time ordering with UUID tie-break; active/revoked records; empty list; exact browser serialization and login-only access | Yes: test_services list cases and test_views connections/browser cases |
| MCPValidator.revoke_token | Real DOT callback for access/refresh tokens, default and explicit hint, expired access token, unknown token noop, foreign-client isolation and disabled-client OAuth denial; access/refresh/delegation state is real | Yes: test_oauth_endpoints revoke cases |
| tasks.dispatch_pending_imports / cleanup_uploads | Due/future queued state; expired/live running lease; done/failed state; disabled/empty queue; disabled cleanup and exact bounded cleanup request; no eager delivery | Yes: test_tasks dispatch/cleanup cases |
| ResourceMetadataView / ServerMetadataView | Exact unauthenticated server/resource metadata, both resource URL aliases, cache/referrer headers, disabled feature 404 | Yes: test_oauth_endpoints metadata cases |
| get_attachment / KickoffView / UploadTokenView | Real root HTTP lifecycle exercises these paths; its coverage is not merged with pytest | Yes, independent HTTP acceptance |
| External MCP client acceptance | Real ChatGPT/Claude/other vendor UI sessions were not performed; synthetic local HTTP acceptance does not prove vendor interoperability | No, explicitly outside this local validation |

Read-only migration check against the isolated pytest DB:
`docker exec -e POSTGRES_DB=test_review_mcp_backend_20261009
review-mcp-backend-20261009 python manage.py makemigrations mcp --check --dry-run`:
No changes detected in app 'mcp'; exit 0.
Final guard source was checked again with the same --check --dry-run command
from /tmp/review_mcp_snapshot/backend after the full PASS: No changes detected
in app 'mcp', exit 0; review_mcp_guard_migrations_final.log. No migration was
created or applied by this check.

Ruff, pycodestyle (79 columns) and git diff --check pass for MCP and modified
existing backend integration paths. Root pre-commit hooks are unchanged and
the Git index remains empty.

Parent-reported independent actual HTTP file lifecycle: 1 passed, 5 warnings,
47.40 seconds; exit 0, `.mcp-validation/review-http-files-stable-final.log`.
The final runtime/storage-helper/root-HTTP manifest has 1196 files; its digest
remained `64e2c4f06f2ca71ff1f1bd99c006befb6294c5dc1ef7fb66efb3db941406f158`.
The run exercised real fieldset SQL shape, byte upload/callback, workflow-scope
attachment ACL with task_id=None, metadata, ticket/Range, refresh/new ticket
200 then revocation 401. Parent owns this independent lifecycle evidence.

## Final OAuth guard validation

The earlier 7282-pass full run and 245-case reconciliation above describe the
pre-guard runtime. The final guard adds 53 local scenarios in the existing
OAuth endpoint, concurrency and configuration test files; total MCP scope is
298 cases. The real shared Redis tests retain isolated per-test prefixes.

| Function/path | Scenario/annotation | Test |
|---|---|---|
| OAuthRateLimitMiddleware._client_ip | Direct IPv4/IPv6; forged XFF/X-Real-IP; trusted right-to-left chains; invalid/empty/oversized/too many hops; empty Unix default unknown; explicit protected Unix trust | Yes: test_oauth_rate__proxy_identity__cannot_escape_existing_budget (13 cases) |
| OAuthRateLimitMiddleware.__call__ | Shared GET/HEAD authorize/login and trailing slash; denial preserves real AuthorizationRequest/LoginCode state; disabled404 never touches Redis | Yes: test_oauth_rate__authorize_login_shared_budget__no_state_change (8 cases), disabled feature case |
| OAuthRateLimitMiddleware._rate_limit_response | Actual Redis concurrent admission exact3of8; saturated count; TTL refusal without extension; expired new window; persistent-key TTL repair; bounded per-IP keys | Yes: four test_concurrency OAuth rate cases |
| Register SDK boundary | Public and confidential clients below quota; actual SQL policy/access token; confidential hash; 429 before hash and all durable writes; exact native error/headers | Yes: registration_within_budget (2 cases), registration_exhausted case |
| Token/revoke SDK boundary | Below-quota refresh creates real checksum-bound access/refresh tokens; denial preserves actual grant/tokens and revocation state | Yes: refresh_within_budget and token_budget_exhausted (2 cases) |
| Redis/configuration failure | Real transport outage/malformed replies; exact eval arguments; Dummy/LocMem unsupported aliases return503; disabled cacheclose with no Redis; bounded URL/window/limits/proxy checks | Yes: outage, malformed (6), unsupported (2), noRedis bootstrap, configuration (11) cases |

```text
docker exec -w /tmp/review_mcp_snapshot/backend -e PYTHONHASHSEED=0
  review-mcp-backend-20261009 python -m pytest src/mcp/tests
  -q -n 4 --dist=loadfile -o 'addopts=--dc=Testing --disable-warnings'
  --reuse-db --basetemp=/tmp/review_mcp_guard_target_final
  --cov=src.mcp --cov-branch
  --cov-report=json:/tmp/review_mcp_guard_coverage_final.json
  --junitxml=/tmp/review_mcp_guard_target_final.xml
```

Result: 298 passed, 20 warnings, 36.47 seconds; exit 0.
Log: backend/.pytest_cache/review_mcp_guard_target_final.log.
Measured guard target production coverage: 1555/1681 statements (92.50%) and
357/456 branches (78.29%), 21 production files, excluding tests/migrations.
The preliminary focused guard run was 92 passed/1 failed/16.76s; its sole
failure compared a raw API refresh token with DOT's compliant hashed SQL token.
The assertion now uses token_checksum=digest(raw). No runtime fix was needed.

The historical explicit-empty environment probe passed before the startup
configuration tests were removed. Log: review_mcp_no_redis.log.

Independent Kant final read-only guard review: 120 passed, 87 warnings, 44.32s;
exit 0, no skips, no confirmed remaining runtime defect. Own separate DB
mcp_final_guard_independent_1009 and unique Redis namespaces; 27 additional
ephemeral independent cases included public/confidential DCR, PKCE, no SQL/hash
on denial, HEAD/slash, exact concurrency count, trusted/forged/Unix identity,
remaining TTL and actual Redis outage. Separate network-none no-Redis
bootstrap/DummyCache/cacheclose/override and enabled wrong-backend503/E006
passed; independent nginx36checks also passed. This evidence was reported by
the independent reviewer, not merged into our pytest coverage.

Final full backend command (all cases, no deselection/skip/middleware bypass):

```text
docker exec -w /tmp/review_mcp_snapshot/backend -e PYTHONHASHSEED=0
  review-mcp-backend-20261009 python -m pytest src -q -n 4 --dist=loadfile
  -o 'addopts=--dc=Testing --disable-warnings' --reuse-db
  --basetemp=/tmp/review_mcp_guard_full_final --cov=src.mcp --cov-branch
  --cov-report=json:/tmp/review_mcp_guard_full_coverage_final.json
  --junitxml=/tmp/review_mcp_guard_full_final.xml
```

Result: **7378 passed, 56 warnings, 368.47 seconds; exit 0**. JUnit independently
confirms 7378 cases, including all 298 MCP cases, zero failures/errors/skips.
This final complete run supersedes the earlier 7282-case baseline for the guard
runtime and includes all 43 local gap cases plus 53 guard/config/bootstrap cases.
Host evidence:

- backend/.pytest_cache/review_mcp_guard_full_final.log
- backend/.pytest_cache/review_mcp_guard_full_final.xml
- backend/.pytest_cache/review_mcp_guard_full_coverage_final.json
- backend/.pytest_cache/review_mcp_guard_code_proof.json

Final measured production MCP coverage: **1556/1681 statements (92.56%)** and
**357/456 branches (78.29%)**, 21 production files; tests/migrations excluded
from the denominator. Every feasible requested local critical path has concrete
scenarios above; external vendor-client acceptance remains explicitly separate.

Original checkout was hashed natively to avoid Windows mount rescans; all 1788
backend source/configuration/fixture files exactly match the Linux snapshot
before and after the full run. Both digests remain
`a215466b540750f4d3fde8dc7749e7ca4e39c0b9cf92380509c3fcb1ab8abbd4`.
The 2028 actual Linux collectstatic files also remain unchanged, digest
`3aff14ffef02cf3fabb2494663d8823c7d074d473b589968c109e408013549ae`.
Strict manifest storage and WhiteNoise middleware remained active. The host's
ignored stale static tree was not modified, and no shared container, database,
Redis state or volume was deleted. Only our isolated test namespaces were used.

No commit, staging, push, CI, deployment, provider delivery or live production
claim is made by this report.
