# Pneumatic connector for Claude: user guide

The Pneumatic connector lets Claude work in your [Pneumatic](https://www.pneumatic.app) account: find and complete your tasks, start workflows from templates, comment, follow up on running workflows, build templates and pull reports — by asking in plain language.

- Connector URL: `https://mcp.pneumatic.app/mcp`
- Works with: Claude.ai (web, desktop and mobile apps) and Claude Code
- Support: [support@pneumatic.app](mailto:support@pneumatic.app)
- Privacy: [connector privacy notice](PRIVACY.md) and the [Pneumatic privacy policy](https://www.pneumatic.app/legal/privacy/)

Self-hosting Pneumatic? Your connector runs on your own server instead of `mcp.pneumatic.app`; see [DEPLOYMENT.md](DEPLOYMENT.md).

## Before you start

You need:

- A Pneumatic account on [my.pneumatic.app](https://my.pneumatic.app).
- A Pneumatic API key. Only **account admins and the account owner** can create API keys. If you are not an admin, ask one to create a key for you or to give you admin rights.
- A Claude plan that supports connectors.

The connector acts **as the user who owns the API key**. Claude sees and changes exactly what that user can see and change in Pneumatic, nothing more. Designing templates, reports across the account and changing users, groups and datasets work only when the key owner is an admin.

## Step 1. Create a Pneumatic API key

1. Sign in to Pneumatic.
2. Open **Integrations → Your API Keys** and press **Create**.
3. Copy the key. The full key is shown only once, right after it is created.

Keep the key private: anyone who has it can act as you in Pneumatic.

## Step 2. Connect Claude

### Claude.ai and the Claude apps

1. Open **Settings → Connectors**.
2. Find **Pneumatic** in the connector directory and press **Connect**. If it is not listed yet, press **Add custom connector**, enter the name `Pneumatic` and the URL `https://mcp.pneumatic.app/mcp`, and add it.
3. A Pneumatic page opens. Paste your API key and press **Allow access**.
4. You return to Claude. The connector is ready.

On Team and Enterprise plans an organization owner may need to add the connector first, after which members connect with their own keys.

Turn the connector on for a chat from the tools menu of the message box if Claude does not use it.

### Claude Code

```bash
claude mcp add --transport http pneumatic https://mcp.pneumatic.app/mcp
```

Run `/mcp` in Claude Code, choose `pneumatic` and authenticate: a browser window opens the same Pneumatic page as above.

## Step 3. Try it

Ask Claude, for example:

- "What is in my Pneumatic inbox? Start with overdue tasks."
- "Open the task 'Approve the invoice' and complete it: approved, amount 1,250."
- "Start the 'Employee onboarding' workflow for Anna Smith, starting on Monday."
- "Which workflows of the 'Client onboarding' template are stuck, and on which step?"
- "Comment on the 'ACME contract' workflow that the signed copy is attached, and attach this file."
- "Snooze the 'Q4 audit' workflow until December 1."
- "Design a template for handling refund requests: request, manager approval, accounting, notify the client."
- "Give me a weekly report: workflows started, completed and overdue."
- "Anna is leaving. Reassign all her tasks to Mark."

Results include links that open the task, workflow or template in Pneumatic.

Claude clients that show MCP prompts also list ready-made scenarios: **triage_inbox**, **weekly_report**, **start_process**, **find_bottlenecks**, **offboard_user** and **design_process**.

## What Claude can do

| Area      | What you can ask for                                                                                                                                                        |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tasks     | List and open your tasks, fill in output fields, tick checklist items, complete or revert tasks, change due dates and performers                                            |
| Workflows | Start workflows from templates, find workflows, read their history, comment, edit kickoff data, snooze, resume, return to a step, finish or terminate                       |
| Templates | Find templates, read kickoff forms, create templates from a description or the template library, add, edit and remove steps and fields, clone and delete templates (admins) |
| Files     | Attach files to tasks, workflows and comments, read attached files                                                                                                          |
| Reports   | Dashboard counters, overdue and highlighted work, statistics per template step, field values across workflows                                                               |
| People    | List users and groups, notifications, vacation; create, update and deactivate users, manage groups and reassign work (admins)                                               |
| Datasets  | List and read datasets; create, update and delete them (admins)                                                                                                             |

Read-only tools are marked as read-only, so Claude can use them without asking. Tools that change data ask for your permission according to your Claude settings.

**Destructive actions** — terminating, finishing or returning a workflow, reverting a task, removing performers, deleting templates, steps, fields, comments, groups or datasets, updating datasets and groups, deactivating users and reassigning their work — are marked as destructive. The connector tells Claude to confirm them with you before calling the tool. Clients that support confirmation forms also show a form with the tool and its arguments, and declining it changes nothing.

Writes are not repeated automatically: if Claude is unsure whether a change went through, it checks the current state in Pneumatic instead of trying again.

## Files

- **Attach a file from a chat:** ask Claude to attach it. Claude uploads text, a file from a public HTTPS link (up to 25 MiB) or a small file it has in the chat (up to 5 MiB).
- **Attach a file from your device:** Claude gives you a one-time upload link valid for one hour. Open it, pick the file (up to 25 MiB), then tell Claude it is uploaded.
- **Read attached files:** Claude reads text files up to 256 KiB and images and other files up to 3 MiB. For larger files it gives you the link.

Files are stored in your Pneumatic account, the same as files attached in the web app.

## Disconnect and revoke access

- **Remove the connector in Claude:** **Settings → Connectors → Pneumatic → Disconnect** (or `claude mcp remove pneumatic` in Claude Code).
- **Revoke the key in Pneumatic:** delete the API key under **Integrations → Your API Keys**. Every Claude session that uses it stops working within 5 minutes, even if it is still connected in Claude.

Revoking the key is the reliable way to cut access off, for example when a device is lost or an employee leaves.

## Troubleshooting

| Problem                                               | What to do                                                                                                                                        |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| The consent page says the key is not valid            | Copy the key again from Pneumatic without spaces. Check that it was not deleted. After 10 wrong keys in a minute, wait a minute.                  |
| You cannot find **Integrations → Your API Keys**      | API keys are available to admins and the account owner. Ask an admin.                                                                             |
| Claude says it is not authorized (`unauthorized`)     | The key was deleted or the account is inactive. Create a new key and reconnect the connector.                                                     |
| Claude says it has no permission (`forbidden`)        | The key owner cannot do this in Pneumatic, for example editing templates without admin rights.                                                    |
| Claude reports a rate limit or that Pneumatic is busy | The connector allows 120 requests per minute per key, and Pneumatic has its own limits. Wait a minute and try again.                              |
| A task cannot be completed                            | Required fields are empty, checklist items are not ticked, the workflow is snoozed or a sub-workflow is still running. Ask Claude what blocks it. |
| Claude does not use Pneumatic                         | Turn the connector on in the chat's tools menu, or mention Pneumatic in the request.                                                              |
| You were asked to connect again                       | Sessions last up to 90 days without use. Connect again with your key.                                                                             |

Still stuck? Write to [support@pneumatic.app](mailto:support@pneumatic.app) with the time of the problem and what you asked Claude. Do not send your API key.
