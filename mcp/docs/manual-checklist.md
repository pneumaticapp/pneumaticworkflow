# Manual verification checklist

Run before a production release, against a disposable Pneumatic account and a staging deployment of the connector. Automated tests use a fake Pneumatic API; these checks cover what only real clients and a real backend can show. Record the connector version, client versions and date with the results.

## 1. Automated checks against the real API

- [ ] `node --env-file=.env --import tsx scripts/smoke.ts` — every read-only endpoint passes.
- [ ] `SMOKE_WRITES=yes node --env-file=.env --import tsx scripts/smoke-write.ts` with an **admin** key of the disposable account — all steps pass and the cleanup steps delete the smoke template and workflow (check in Pneumatic that nothing is left).

## 2. Deployment

- [ ] `/healthz` returns `{"status":"ok"}`; the metadata endpoints show the public HTTPS URLs; `POST /mcp` without a token returns 401 with `WWW-Authenticate`.
- [ ] `PNEUMATIC_FILES_URL` matches the backend's `FILE_SERVICE_URL`: a link returned by `upload_file` opens in a browser signed in to Pneumatic, and `webUrl` links open the right task, workflow and template.
- [ ] Logs are JSON lines on stderr and contain no API keys, tokens, upload links or tool arguments (search the logs for `pn-`, `pmcp_` and `/upload/`).
- [ ] With `METRICS_TOKEN` set, `/metrics` returns 401 without the token and Prometheus text with it.
- [ ] Restart the container: existing sessions keep working and spent refresh tokens stay rejected (the replay ledger is on the volume).

## 3. Claude.ai custom connector

- [ ] Add the connector with the `/mcp` URL; the consent page opens, shows the client name, and **Allow access** with a valid key returns to Claude (this exercises the browser `Origin` handling of the consent form).
- [ ] A wrong key shows the rejection message on the consent page; eleven wrong keys within a minute return 429.
- [ ] The tool list matches `TOOLSETS` / `READ_ONLY`; prompts (`triage_inbox`, `start_process`, …) appear if the client shows prompts.
- [ ] Read: "What is in my Pneumatic inbox?" returns tasks with working links and names.
- [ ] Write: start a workflow from a template and complete a task with a dropdown and a date field; an invalid option is explained instead of failing with a generic error.
- [ ] Destructive tool: ask to terminate a workflow. Note whether Claude.ai shows a confirmation form; if it does, **Decline** leaves the workflow untouched (`cancelled`) and **Accept** terminates it. If no form appears, Claude must still ask in the chat before calling the tool.
- [ ] Files: attach a file from the device through `create_upload_link` (the upload page accepts it once and then reports the link as used), then put it into a file field; download an image and a text file with `download_file`.
- [ ] Revoke the API key in Pneumatic: within 5 minutes tool calls fail with `unauthorized`.
- [ ] Leave the session idle for more than an hour (access token lifetime): the next call refreshes the token without a new consent.

## 4. Claude Code

- [ ] Remote with OAuth (`claude mcp add --transport http …`): browser consent completes and tools work.
- [ ] Remote with a static key header and local stdio (`PNEUMATIC_API_KEY`): tools work; in stdio the logs go to stderr only.
- [ ] Destructive tool in an interactive session: note whether a confirmation form appears and that declining changes nothing. In a non-interactive run (`claude -p`), note whether destructive tools are declined automatically.

## 5. Configuration variants

- [ ] `READ_ONLY=true`: only read tools are listed and Claude explains that changes must be made in Pneumatic.
- [ ] `TOOLSETS=core`: design, analytics, files and admin tools are absent and the instructions do not mention them.
- [ ] `RATE_LIMIT_PER_MINUTE=5`: the sixth request within a minute returns 429 with `Retry-After`.
