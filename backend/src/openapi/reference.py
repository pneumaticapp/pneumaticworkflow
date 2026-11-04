"""Static API reference content, safe to import while settings load."""

API_DESCRIPTION = r"""
The complete Pneumatic API reference covers product operations, public forms,
identity providers, billing callbacks and internal services. A documented
operation still enforces its existing role, account, feature and source-IP
restrictions. Internal and staging operations are not general API-key APIs.
Paths are relative to the deployment root and normally have no trailing slash.

### Authentication

Use `Authorization: Bearer <api_key>` for automation. API keys start with
`pn-`; create, expire and revoke them through the account API-key operations.
Keys are displayed in the app's Integrations section. Their permissions are
those of their user; a key does not bypass subscription or object checks.

`POST /auth/token/obtain` accepts `username` (email) and `password` and returns
a Pneumatic session `token`, not a JWT pair. Pass it as
`Authorization: Bearer <token>`. The separate `/auth/token/refresh` operation
accepts a valid refresh JWT and returns a new access JWT; it cannot refresh
an opaque session token or API key. Expiration and revocation depend on the
token type and the issuing operation; do not assume tokens are interchangeable.

Public forms use `X-Public-Authorization: Token <public_id_or_embed_id>`.
The literal `Token ` prefix is required. Obtain the public/embed ID from a
template with public/embedded access enabled. Public template access does not
authenticate an account user. Guests use `X-Guest-Authorization: <guest_jwt>`
without a prefix, from their assigned task link. Guest access is restricted
to the assigned task and the workflow operations permitted by that assignment.
The security alternatives and Access section of each operation apply together.

When PRIVATE_API_CHECK_IP is enabled, operations guarded by
PrivateApiPermission reject API keys even from an allowlisted IP. User-session
and JWT credentials must pass the source-IP whitelist. With the check disabled,
the operation's other role and account permissions still apply.

Sign-up, selected password/identity-provider operations, CMS pages and inbound
callbacks have their own authentication and feature gates. Customer.io uses
signature/timestamp headers; Okta backchannel logout uses an Okta provider
token.
Refer to those operations instead of sending a Pneumatic API key to callbacks.
Browser-cookie authentication documented by Files API is specific to that
service; it is not a cookie-authentication option for arbitrary Core writes.

### Dates and dynamic fields

Fields ending in `_tsp` use Unix seconds, for example `1767225600.0`.
They are numbers in responses, with `null` where the underlying date is unset.
Core timestamp request fields also accept numeric strings. ISO date-time
strings are not accepted by `TimeStampField`. Date values inside dynamic fields
must be JSON numbers.

`POST /templates/{id}/run` supplies kickoff values in `kickoff`;
`PATCH`/`PUT /workflows/{id}` updates kickoff values; and
`POST /v2/tasks/{id}/complete` supplies task values in `output`.
These objects are keyed by the field's `api_name`, never its display label.
Read the template/task field metadata first: `type`, `is_required`, available
`selections` and dataset values determine the valid payload.

| Field type | JSON input |
| --- | --- |
| `string` | String, at most 140 characters. |
| `text` | String; Markdown is supported. |
| `number` | Decimal-compatible JSON number or numeric string. |
| `date` | Unix seconds as a JSON number. |
| `radio`, `dropdown` | One configured selection/dataset value string. |
| `checkbox` | Array of configured selection/dataset value strings. |
| `url` | URL string accepted by the URL validator. |
| `file` | Array of Markdown links `[filename](file_service_url)`. |
| `user` | Account user's email or group name string, case insensitive. |

File links must point to this deployment's configured file service. Upload the
file first, then use its returned URL in a Markdown link; a bare file ID is not
a valid dynamic file-field value. Empty `null`, `""` or `[]` clears an optional
field and is rejected for a required field. Omitting a field and explicitly
clearing it are different operations; use the current template/task metadata
and the target operation's schema.

For a template whose fields have the corresponding API names and choices:
```json
{"kickoff":{"employee-name":"Jane Doe","budget":"1250.50",
"start-date":1767225600,"departments":["Engineering"],
"manager":"manager@example.com"}}
```
Task completion requires a running workflow and an active task, required output
values, marked required checklists and completed child workflows. Revert
requires an eligible completed task and a nonempty comment. Finish requires a
workflow that can be finalized. Object access alone does not guarantee that a
state-changing operation is valid in the resource's current state.

### Responses, pagination and errors

An empty successful Core `response_ok()` is `204 No Content`; it has no JSON
body. Data-bearing successes are usually `200`, with `201` where documented.
List response shapes vary: some are arrays, others use
`count`, `next`, `previous`, `results`. Consult the response schema rather than
assuming every list is paginated. `limit` and `offset` are available only where
listed. Query parameters list accepted enum values; examples use those values.

Core validation errors normally contain `message`, `code`, and optional
`details` identifying a field by `name` or `api_name` and `reason`.
Authentication/permission/not-found errors normally contain `detail`.
Some legacy routes return empty error bodies or HTML redirects as documented.
Files API has its own error model and a separate throttling response. Respect
`429` and `Retry-After` where returned. Rate-limit scopes and rates are
deployment settings; there is no single global fixed API request quota.

### Webhook delivery

The supported events are `workflow_started`, `workflow_completed`,
`task_completed` and `task_returned`. Subscription operations configure an
outgoing JSON HTTP POST to your endpoint. The payload contains `hook` metadata
and a `workflow` or `task` object; the webhook-example operations provide its
shape. Subscribing to all events replaces the account's existing
subscriptions;
unsubscribing from all events removes them. Event-specific operations affect
the selected event.

Delivery is asynchronous through Celery. Connection/HTTP exceptions and
recipient responses >=500 are retried, with exponential backoff and at most
two retries per task. Other unsuccessful responses are logged without the
same automatic retry. Task-level retry can resend to an endpoint that already
received an earlier attempt, so consumers must tolerate duplicates. No
exactly-once delivery, ordering or request-signature guarantee is provided by
the outgoing webhook implementation. Do not confuse it with signed incoming
Customer.io callbacks.

### WebSocket events

Connect to `ws(s)://<deployment-host>/ws/events?auth_token=<session_token>`.
Use the opaque Pneumatic user-session token; anonymous connections are denied.
The server joins the authenticated user's event group and sends JSON event
notifications. Send the text `PING` to receive the text `PONG`; heartbeat
frames are not JSON. Notifications carry the event-specific object delivered
to that user (for example changed task/workflow information); read the event's
payload rather than assuming a REST response envelope.

Clients should reconnect after disconnection and reload REST state. The
WebSocket protocol has no client acknowledgement, cursor, replay or durable
delivery contract. The token is in the connection URL, so avoid recording the
full URL in client logs. REST mutations remain separate HTTP operations.

### Core and Files schemas

`/api/schema/` is the complete Core schema. Files API publishes
`/files/openapi.json`. This reference page merges both documents; each raw
schema remains available for its own service. File downloads return binary
content and support Range responses, not a JSON file body. See the Files
operations for multipart uploads, authentication, limits and response headers.
"""

HEADER_SECURITY_SCHEMES = {
    'publicTemplateAuth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-Public-Authorization',
        'description': (
            'Public or embedded template token. Enter the complete value '
            '`Token <public_id_or_embed_id>`, including the Token prefix. '
            'Only operations allowing public template access accept it.'
        ),
    },
    'guestAuth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-Guest-Authorization',
        'description': (
            'Raw guest JWT from a guest task link; do not add Bearer. '
            'Access is restricted to the assigned task and permitted '
            'workflow operations.'
        ),
    },
    'oktaLogoutAuth': {
        'type': 'http',
        'scheme': 'bearer',
        'bearerFormat': 'JWT',
        'description': (
            'Okta provider backchannel logout token, not a Pneumatic '
            'user token or API key.'
        ),
    },
    'customerIOSignature': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-CIO-Signature',
        'description': (
            'Customer.io webhook HMAC signature; also requires '
            'X-CIO-Timestamp and the unmodified request body.'
        ),
    },
}
