# Claude Connectors Directory submission

Answers for the developer portal at [claude.ai/directory/manage](https://claude.ai/directory/manage) (**Submit new → MCP connector**), following the steps of [Anthropic's submission guide](https://claude.com/docs/connectors/building/submission). Keep this file in sync with the published listing. Never put the reviewer account's credentials here: enter them only in the portal.

## 1. Connection

- Server URL: `https://mcp.pneumatic.app/mcp`
- Users connect to one URL. Self-hosted Pneumatic instances run their own connector and add it as a custom connector.

## 2. Tools

68 tools, each with a `title` and a `readOnlyHint` or `destructiveHint` annotation (checked by `test/catalog.test.ts`), plus 6 prompts. Read-only tools carry `readOnlyHint: true`; destructive tools carry `destructiveHint: true`.

## 3. Listing

**Name:** Pneumatic

**One-liner (≤ 200):**

> Run workflows, complete tasks and build process templates in Pneumatic by asking Claude in plain language.

**Description (≤ 2,000):**

> Pneumatic is a workflow management system for teams that run repeatable processes: onboarding, approvals, client projects, purchasing and more. The Pneumatic connector lets Claude work in your Pneumatic account with your permissions.
>
> Ask Claude what is in your task inbox, open a task and complete it with the right field values, or start a workflow from a template with its kickoff form filled in. Follow up on running workflows: read their history, comment, attach files, change due dates and performers, snooze, resume or return a workflow to an earlier step.
>
> Admins can describe a process and have Claude build the template — steps, performers, output fields, checklists and due dates — or start from the template library, then refine steps and fields in conversation. Claude can also pull dashboard numbers, find overdue and stuck work, compare field values across workflows, manage users, groups and datasets, and reassign an employee's work when they leave.
>
> The connector checks field values against your forms before writing, so mistakes come back as clear explanations, and results include links that open tasks, workflows and templates in Pneumatic. Destructive actions such as terminating workflows or deleting templates are marked as destructive, and Claude is instructed to confirm them with you first.
>
> You sign in with a Pneumatic API key. The connector acts only with that user's permissions, stores no Pneumatic data, and access ends as soon as the key is deleted in Pneumatic.

**Categories:** Productivity; Project management (pick the closest options the portal offers).

**Documentation URL:** `https://github.com/pneumaticapp/pneumaticworkflow/blob/master/mcp/docs/USER_GUIDE.md`

**Privacy policy URL:** `https://github.com/pneumaticapp/pneumaticworkflow/blob/master/mcp/docs/PRIVACY.md` (it refers to `https://www.pneumatic.app/legal/privacy/`)

**Support contact:** `support@pneumatic.app`

**Icon:** square Pneumatic logo (PNG or SVG, transparent background).

**Slug:** `pneumatic` (permanent once published).

## 4. Use cases

Primary use cases:

1. Work through the task inbox: find assigned tasks, fill in output fields and complete them.
2. Start workflows from templates with kickoff data and attachments.
3. Track and manage running workflows: status, comments, due dates, performers, snooze and return.
4. Design process templates from a description or the template library.
5. Reporting: overdue and stuck work, step statistics, weekly summaries.
6. Team administration: users, groups, datasets and reassigning work during offboarding.

Before connecting, users need a Pneumatic account at `my.pneumatic.app` and an API key created by an account admin or the account owner (**Integrations → Your API Keys**).

The connector reads and writes data.

## 5. Company

- Company: Pneumatic Software Inc.
- Website: `https://www.pneumatic.app`
- Primary contact: the person responsible for the listing (an email that receives review updates).

## 6. Authentication

- Authentication requirement: **Required**.
- Method: OAuth 2.1 with dynamic client registration (`/register`) and PKCE S256. The authorization page asks the user for their Pneumatic API key. No Anthropic-held client ID or secret is needed.
- Discovery: `/.well-known/oauth-protected-resource/mcp` and `/.well-known/oauth-authorization-server`.
- Redirect hosts allowed: `claude.ai`, `claude.com`, loopback.

## 7. Data handling

- The underlying API is our own (Pneumatic).
- No personal health data and no sponsored content.

## 8. Test & launch

Reviewer account to prepare on `my.pneumatic.app` before submitting:

- An admin user of a dedicated test account (admin rights are needed for design, analytics and admin tools).
- At least two other users and one group, so assignment and reassignment can be tested.
- Three or more active templates with kickoff fields of several types (text, dropdown, date, file), including one with a checklist.
- Running workflows with active and overdue tasks assigned to the reviewer, plus finished workflows, comments and attachments.
- One dataset.
- An API key for the reviewer admin created under **Integrations → Your API Keys**.

Instructions for reviewers (enter in the portal with the credentials):

1. Add the connector with the URL `https://mcp.pneumatic.app/mcp`.
2. On the Pneumatic authorization page paste the API key provided and press **Allow access**.
3. Optionally sign in at `https://my.pneumatic.app` with the email and password provided to see the same data in the web app.
4. Try: "What is in my Pneumatic inbox?", "Start the <template> workflow", "Complete the task <name>", "Which workflows are overdue?", "Create a template for handling refund requests".

Before submitting, call every tool from Claude with the custom connector and run [manual-checklist.md](manual-checklist.md) section 3 against `mcp.pneumatic.app`.

## 9. Compliance

All seven acknowledgments are required. Relevant facts:

- Uses only Pneumatic's own API; no financial transactions; no AI media generation.
- Tool descriptions and server instructions contain no instructions aimed at other tools or connectors; tool results are data returned from Pneumatic.
- The connector does not collect Claude conversation data; it receives only tool arguments and keeps no copy of them.
- Documentation is public: [USER_GUIDE.md](USER_GUIDE.md) and [PRIVACY.md](PRIVACY.md).
