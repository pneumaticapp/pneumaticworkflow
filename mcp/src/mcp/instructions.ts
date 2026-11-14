import { formatMiB, MAX_INLINE_UPLOAD_BYTES, MAX_UPLOAD_BYTES } from '../core/files.js';
import { STRING_LIMIT } from '../core/limits.js';
import type { ToolDef } from './toolDef.js';

const DUPLICATING_WRITE_EXAMPLES = ['run_workflow', 'upload_file'];

export function buildInstructions(tools: readonly ToolDef[]): string {
  const names = new Set(tools.map(({ name }) => name));
  const has = (...wanted: string[]) => wanted.some((name) => names.has(name));
  const hasWrites = tools.some(({ annotations }) => annotations.readOnlyHint !== true);
  const destructive = tools.filter(({ annotations }) => annotations.destructiveHint).map(({ name }) => name);
  const duplicatingWrites = DUPLICATING_WRITE_EXAMPLES.filter((name) => names.has(name));
  const fileTargets = [
    has('complete_task') && 'complete_task output',
    has('run_workflow') && 'run_workflow kickoff',
    has('update_workflow') && 'update_workflow kickoff',
  ].filter(Boolean);

  const sections = [
    `Pneumatic is a workflow management system.
- A template is a reusable process blueprint: a kickoff form plus ordered task steps.
- A workflow is a running instance of a template; its tasks are assigned to users, groups or guests.
- Tasks have output fields that performers fill in when completing them.
The connector acts with the permissions of the Pneumatic user who owns the API key.`,

    `Results: read structuredContent.data (or parse the JSON text). Lists return data.items and data.page; pass
offset=data.page.nextOffset for more until it is null. If truncated is true, the result was shortened: do not
treat it as complete and do not copy truncated values back into writes. A failed call carries
structuredContent.error {code, message, retryable, detail}; detail holds Pneumatic's own validation message.
Arguments that violate the input schema (including unknown keys) fail with a plain-text error instead.
Template, workflow and task IDs are different numeric IDs; template steps are not workflow task instances.
Dates in inputs and results are ISO 8601 (UTC in results${has('get_current_user') ? "; the user's timezone is in get_current_user" : ''}).
Results carry webUrl links to open tasks, workflows and templates in Pneumatic, and people's names next to IDs;
share these links with the user instead of describing where to click.`,

    hasWrites
      ? `Writes are not idempotent: repeating ${[...duplicatingWrites, 'a create or comment call'].join(', ')} creates another
object. After an uncertain write result, check the current state before retrying.`
      : `This connector is read-only: it can look things up but not change them. When the user asks for a change, say
what would need to be done in Pneumatic instead of attempting it.`,

    [
      'Workflows and tasks:',
      has('run_workflow') &&
        `- To start a workflow: list_templates (check isActive) -> get_template_kickoff -> run_workflow. get_template is
an owner/admin overview and is not needed to launch. Use the returned workflow id with get_workflow.`,
      has('list_tasks') &&
        `- Assigned work: list_tasks -> get_task (description, output fields, checklists)${has('complete_task') ? ' -> complete_task' : ''}.`,
      has('list_tasks', 'list_workflows', 'get_workflow') &&
        '- Workflow status: running, done, snoozed. Task status: pending, active, completed, snoozed, skipped.',
      has('list_workflows') && '- list_workflows can return field values (fieldApiNames) to compare workflows.',
      has('complete_task', 'run_workflow') &&
        `- Write kickoff/output maps with each field's apiName as a top-level key, including fields inside fieldsets.
Required kickoff values must be sent; defaults are not applied to omitted fields. Value formats: string/text/url
-> string (string max ${STRING_LIMIT} chars); number -> number; date -> ISO 8601 date-time; radio/dropdown -> one selections value;
checkbox -> array of selections values; user -> user email or group name; file -> array of "[name](url)" links.
Do not blindly echo read values: checkbox and user values are represented differently on reads. The connector
checks writes against the form first and explains unknown keys, invalid options and empty required fields.
- complete_task changes only supplied fields. Unfinished checklists (set_checklist_item), a snoozed workflow or
running sub-workflows block completion. With several required performers the task may stay active after a
successful completion; inspect the result and get_workflow instead of repeating the call.
- comment_on_task targets a task; comment_on_workflow picks the active task with the highest step number.`,
      has('list_users') && '- Resolve people with list_users / list_groups before assigning performers.',
      destructive.length > 0 && `- Before any destructive tool (${destructive.join(', ')}), confirm with the user.`,
    ],

    has('create_template') && [
      'Designing processes (admins):',
      `- create_template builds a template from steps; steps run one after another unless sequential=false. Use
generate_template_steps or list_library_templates / create_template_from_library for a starting point, and
show the proposed steps to the user before creating. Change existing templates with add_template_step,
update_template_step, remove_template_step, update_template_kickoff and remove_template_fields (step and field
api names come from ${has('get_template') ? 'get_template' : 'the template'}); update_template changes settings,
activation and public forms.`,
      has('list_users') && '- Use list_users / list_groups for performer IDs and list_datasets for option lists.',
    ],

    has('get_dashboard', 'get_template_step_stats') &&
      `Analytics: get_dashboard and list_highlights for periods, get_template_step_stats for bottlenecks per step,
count_workflows for workload, get_workflow_field_values (account owner) for values across workflows.`,

    [
      'People:',
      has('list_notifications') && '- list_notifications shows what is new for the connected user.',
      has('set_vacation') && '- set_vacation delegates tasks to substitutes while someone is away.',
      has('reassign_user') &&
        `- reassign_user permanently hands over everything; deactivate_user fails while the user is the last performer
somewhere, so check get_assignment_count first.`,
    ],

    has('download_file', 'upload_file') && [
      'Files:',
      has('download_file') &&
        `- Read: file fields expose fileLinks in task output and workflow kickoff values; comments contain
"[name](url)" links; list_attachments lists accessible files. Pass a link or fileId to download_file. It returns
images inline, small text as text and other files as base64 resources; for large files it returns only the url
to open in a browser signed in to Pneumatic.`,
      has('upload_file') &&
        `- Write: upload_file (contentText or contentBase64 up to ${formatMiB(MAX_INLINE_UPLOAD_BYTES)}, or a public HTTPS sourceUrl up to ${formatMiB(MAX_UPLOAD_BYTES)})
returns data.fieldValue, a "[name](url)" link. Do not invent file contents.${
          fileTargets.length
            ? ` Attach a link via ${fileTargets.join(', ')} as {"field_api_name": ["[name](url)"]}, or paste the link
into a comment. A supplied file field REPLACES its saved files: to keep them, send the existing fileLinks together
with the new links; [] clears the field.`
            : ''
        }`,
      has('create_upload_link') &&
        `- For a file on the user's device (e.g. attached in the chat), use create_upload_link: give the user
data.uploadUrl, then poll get_upload_status until ready and use data.file.fieldValue.`,
    ],
  ];

  return sections
    .map((section) => (Array.isArray(section) ? section.filter(Boolean) : section))
    .filter((section) => (Array.isArray(section) ? section.length > 1 : Boolean(section)))
    .map((section) => (Array.isArray(section) ? section.join('\n') : section))
    .join('\n\n');
}
