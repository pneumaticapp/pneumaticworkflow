import * as z from 'zod/v4';

import type { PneumaticClient } from '../pneumatic/client.js';

import { tool, type ToolDef } from '../mcp/toolDef.js';
import { fieldSpecs, prepareFieldValues } from './fields.js';
import { isRecord } from '../core/json.js';
import {
  compactFor,
  additive,
  commentText,
  dateTime,
  destructive,
  done,
  fieldValues,
  id,
  idempotentUpdate,
  limit,
  offset,
  readOnly,
  requireExactlyOne,
  toTimestamp,
} from './shared.js';

const taskId = id('Task').describe('Workflow task instance ID, not a template step');

const performer = z.strictObject({
  taskId,
  userId: id('User').optional(),
  groupId: id('Group').optional(),
  guestEmail: z.email().optional().describe('External guest performer; only for adding/removing guests'),
});

type Performer = z.infer<typeof performer>;

function performerRequest(action: 'create' | 'delete', performer: Performer) {
  requireExactlyOne(performer, ['userId', 'groupId', 'guestEmail']);
  const { userId, groupId, guestEmail } = performer;
  if (userId !== undefined) {
    return { path: `${action}-performer`, body: { user_id: userId } };
  }
  if (groupId !== undefined) {
    return { path: `${action}-group-performer`, body: { group_id: groupId } };
  }
  return { path: `${action}-guest-performer`, body: { email: guestEmail } };
}

async function taskDetail(client: PneumaticClient, raw: unknown) {
  const compact = await compactFor(client, { people: true });
  return compact.out(compact.taskDetail(raw));
}

export const taskTools: ToolDef[] = [
  tool(
    'list_tasks',
    {
      title: 'List tasks',
      description:
        "List tasks from the current user's inbox (active by default, including group assignments) with " +
        "pagination. Admins can pass assignedTo to see another user's tasks. Call get_task before working on a task.",
      inputSchema: z.strictObject({
        isCompleted: z.boolean().default(false).describe('true = completed tasks, false = active tasks'),
        search: z.string().max(200).optional().describe('Search by task or workflow name'),
        templateId: id('Template').optional(),
        templateTaskApiName: z.string().optional().describe('Only tasks of this template step'),
        assignedTo: id('User').optional().describe('User ID (admins only)'),
        ordering: z
          .enum(['date', '-date', 'overdue', '-overdue', 'completed', '-completed'])
          .optional()
          .describe('date = started date, overdue = due date, completed = completion date; "-" = descending'),
        limit,
        offset,
      }),
      annotations: readOnly,
    },
    async (args, { client }) => {
      const raw = await client.get('/v3/tasks', {
        is_completed: args.isCompleted,
        search: args.search,
        template_id: args.templateId,
        template_task_api_name: args.templateTaskApiName,
        assigned_to: args.assignedTo,
        ordering: args.ordering,
        limit: args.limit,
        offset: args.offset,
      });
      const compact = await compactFor(client);
      return compact.out(compact.page(raw, args, (item) => compact.task(item)));
    },
  ),

  tool(
    'get_task',
    {
      title: 'Get task',
      description:
        'Get task state, description, output fields (api names, types, required flags, selections and current ' +
        'values; file fields list fileLinks), checklists, performers, due date and the parent workflow. Read it ' +
        'before complete_task and use field api names, not labels. Read access alone does not grant completion permission.',
      inputSchema: z.strictObject({ taskId }),
      annotations: readOnly,
    },
    async ({ taskId }, { client }) => taskDetail(client, await client.get(`/v2/tasks/${taskId}`)),
  ),

  tool(
    'list_task_events',
    {
      title: 'List task events',
      description:
        'List the activity of one task, newest first, with pagination: comments, completions, returns, ' +
        'performer and due-date changes, delegations. Comment events can be edited or reacted to by id.',
      inputSchema: z.strictObject({
        taskId,
        includeComments: z.boolean().default(true),
        onlyAttachments: z.boolean().optional().describe('true = only events with files'),
        limit,
        offset,
      }),
      annotations: readOnly,
    },
    async ({ taskId, includeComments, onlyAttachments, limit, offset }, { client }) => {
      const raw = await client.get(`/v2/tasks/${taskId}/events`, {
        include_comments: includeComments,
        only_attachments: onlyAttachments,
        limit,
        offset,
      });
      const compact = await compactFor(client, { people: true });
      return compact.out(compact.page(raw, { limit, offset }, (item) => compact.event(item)));
    },
  ),

  tool(
    'complete_task',
    {
      title: 'Complete task',
      description:
        'Submit completion of an active task for the current user. Read get_task first; output changes only the ' +
        'supplied fields, and a supplied file field replaces its saved files (include existing fileLinks to keep ' +
        'them). Unfinished checklists, a snoozed workflow or running sub-workflows can block completion. With ' +
        'several required performers the task can stay active after this completion: inspect the returned task ' +
        'and get_workflow before claiming the workflow moved on. May notify people or trigger integrations. ' +
        'Do not blindly retry after an uncertain result.',
      inputSchema: z.strictObject({ taskId, output: fieldValues.optional() }),
      annotations: additive,
    },
    async ({ taskId, output }, { client }) => {
      const current = await client.get(`/v2/tasks/${taskId}`);
      const specs = isRecord(current) ? fieldSpecs(current.output, current.fieldsets) : [];
      const prepared = prepareFieldValues(specs, output, { checkRequired: 'unfilled' });
      return taskDetail(client, await client.post(`/v2/tasks/${taskId}/complete`, { output: prepared }));
    },
  ),

  tool(
    'revert_task',
    {
      title: 'Revert task',
      description:
        'Send the workflow back from this ACTIVE task to the previous step (e.g. to request changes). ' +
        'A comment explaining why is required. It cannot undo a completed task; use return_workflow_to_task for that.',
      inputSchema: z.strictObject({ taskId, comment: commentText }),
      annotations: destructive,
    },
    async ({ taskId, comment }, { client }) => {
      await client.post(`/v2/tasks/${taskId}/revert`, { comment });
      return done();
    },
  ),

  tool(
    'comment_on_task',
    {
      title: 'Comment on task',
      description:
        'Add a nonblank comment to an active or snoozed task of a workflow that is not completed. Supports ' +
        'Markdown; mention users as [Name|user_id]; attach files as "[name](url)" links from upload_file. It does ' +
        'not complete the task and may notify people. Repeating the call creates another comment.',
      inputSchema: z.strictObject({ taskId, text: commentText }),
      annotations: additive,
    },
    async ({ taskId, text }, { client }) => {
      const compact = await compactFor(client, { people: true });
      return compact.out(compact.event(await client.post(`/v2/tasks/${taskId}/comment`, { text })));
    },
  ),

  tool(
    'set_task_due_date',
    {
      title: 'Set task due date',
      description: 'Set the due date of an active task, or pass null to remove it.',
      inputSchema: z.strictObject({ taskId, dueDate: dateTime.nullable() }),
      annotations: idempotentUpdate,
    },
    async ({ taskId, dueDate }, { client }) => {
      if (dueDate === null) {
        await client.delete(`/v2/tasks/${taskId}/due-date`);
      } else {
        await client.post(`/v2/tasks/${taskId}/due-date`, { due_date_tsp: toTimestamp(dueDate) });
      }
      return done();
    },
  ),

  tool(
    'add_task_performer',
    {
      title: 'Add task performer',
      description: 'Assign a user, a group or an external guest (by email) to a task. Provide exactly one of them.',
      inputSchema: performer,
      annotations: idempotentUpdate,
    },
    async (args, { client }) => {
      const { path, body } = performerRequest('create', args);
      const raw = await client.post(`/v2/tasks/${args.taskId}/${path}`, body);
      const compact = await compactFor(client);
      return raw === null ? done() : compact.out({ success: true, guest: compact.user(raw) });
    },
  ),

  tool(
    'remove_task_performer',
    {
      title: 'Remove task performer',
      description: 'Unassign a user, a group or a guest from a task. Provide exactly one of them.',
      inputSchema: performer,
      annotations: destructive,
    },
    async (args, { client }) => {
      const { path, body } = performerRequest('delete', args);
      await client.post(`/v2/tasks/${args.taskId}/${path}`, body);
      return done();
    },
  ),

  tool(
    'set_checklist_item',
    {
      title: 'Check or uncheck checklist item',
      description:
        'Mark or unmark a checklist item of a task. checklistId and selectionId come from the checklists of get_task.',
      inputSchema: z.strictObject({
        checklistId: id('Checklist'),
        selectionId: id('Checklist item (selection)'),
        checked: z.boolean(),
      }),
      annotations: idempotentUpdate,
    },
    async ({ checklistId, selectionId, checked }, { client }) => {
      const raw = await client.post(`/v2/tasks/checklists/${checklistId}/${checked ? 'mark' : 'unmark'}`, {
        selection_id: selectionId,
      });
      const compact = await compactFor(client);
      return raw === null ? done() : compact.out(compact.checklist(raw));
    },
  ),
];
