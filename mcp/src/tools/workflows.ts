import * as z from 'zod/v4';

import { ConnectorError } from '../core/errors.js';
import { isRecord } from '../core/json.js';
import { tool, type ToolDef } from '../mcp/toolDef.js';
import { additive, destructive, idempotentUpdate, readOnly } from './annotations.js';
import { optionalTimestamp, toTimestamp } from './dates.js';
import { workflowDetail } from './details.js';
import { fieldSpecs, prepareFieldValues } from './fields.js';
import { present, successOutput } from './output.js';
import { commentText, dateTime, fieldValues, id, idList, limit, offset } from './schemas.js';

const workflowId = id('Workflow').describe('Workflow instance ID, not its template ID');

export const workflowTools: ToolDef[] = [
  tool(
    'list_workflows',
    {
      title: 'List workflows',
      description:
        'List workflow summaries (running process instances) with their tasks, performers and due dates, with ' +
        'pagination. Performer filters work only with status "running". Use get_workflow for kickoff values.',
      inputSchema: z.strictObject({
        status: z.enum(['running', 'snoozed', 'done']).optional(),
        search: z.string().max(200).optional().describe('Full-text search by workflow name'),
        templateIds: idList('Template').optional(),
        currentPerformerIds: idList('User').optional().describe('Workflows where these users have an active task'),
        currentPerformerGroupIds: idList('Group').optional(),
        workflowStarterIds: idList('User').optional().describe('Workflows started by these users'),
        isExternal: z.boolean().optional().describe('true = started from a public form'),
        templateTaskApiName: z
          .string()
          .max(200)
          .optional()
          .describe('Only workflows whose current step is this template step (with templateIds)'),
        fieldApiNames: z
          .array(z.string().min(1).max(200))
          .max(20)
          .optional()
          .describe('Return these kickoff/output field values in items[].fields, e.g. to compare amounts'),
        ordering: z
          .enum(['-date', 'date', '-urgent', 'overdue'])
          .optional()
          .describe('-date newest first, date oldest first, -urgent urgent first, overdue overdue first'),
        limit,
        offset,
      }),
      annotations: readOnly,
    },
    async (args, { client }) => {
      const raw = await client.get('/workflows', {
        status: args.status,
        search: args.search,
        template_id: args.templateIds,
        current_performer: args.currentPerformerIds,
        current_performer_group_ids: args.currentPerformerGroupIds,
        workflow_starter: args.workflowStarterIds,
        is_external: args.isExternal,
        template_task_api_name: args.templateTaskApiName,
        fields: args.fieldApiNames,
        ordering: args.ordering,
        limit: args.limit,
        offset: args.offset,
      });
      return present(client, (presenter) => presenter.page(raw, args, (item) => presenter.workflow(item)), {
        shouldLoadPeople: true,
      });
    },
  ),

  tool(
    'get_workflow',
    {
      title: 'Get workflow',
      description:
        'Get workflow state, kickoff field values and its tasks (skipped tasks excluded). Status is running, done ' +
        'or snoozed; task status is pending, active, completed, snoozed or skipped. Call get_task for a task output ' +
        'form. Check truncated before treating returned details as complete. Reading a workflow does not grant ' +
        'permission to complete its tasks.',
      inputSchema: z.strictObject({ workflowId }),
      annotations: readOnly,
    },
    async ({ workflowId }, { client }) => workflowDetail(client, await client.get(`/workflows/${workflowId}`)),
  ),

  tool(
    'list_workflow_events',
    {
      title: 'List workflow events',
      description:
        'List the workflow activity feed, newest first, with pagination: started/completed tasks, returns, snoozes, ' +
        'performer changes and comments (files appear as Markdown links in text). The workflow-run event is ' +
        'excluded. Use it to inspect progress or to reconcile an uncertain comment before retrying.',
      inputSchema: z.strictObject({
        workflowId,
        includeComments: z.boolean().default(true),
        onlyAttachments: z.boolean().optional().describe('true = only events with files'),
        limit,
        offset,
      }),
      annotations: readOnly,
    },
    async ({ workflowId, includeComments, onlyAttachments, limit, offset }, { client }) => {
      const raw = await client.get(`/workflows/${workflowId}/events`, {
        include_comments: includeComments,
        only_attachments: onlyAttachments,
        limit,
        offset,
      });
      return present(client, (presenter) => presenter.page(raw, { limit, offset }, (item) => presenter.event(item)), {
        shouldLoadPeople: true,
      });
    },
  ),

  tool(
    'comment_on_workflow',
    {
      title: 'Comment on workflow',
      description:
        'Add a nonblank comment to a workflow that is not completed. Pneumatic attaches it to the active or ' +
        'snoozed task with the highest step number; use comment_on_task to target a specific task. Supports ' +
        'Markdown; mention users as [Name|user_id]; attach files as "[name](url)" links from upload_file. ' +
        'May notify people. Repeating the call creates another comment.',
      inputSchema: z.strictObject({ workflowId, text: commentText }),
      annotations: additive,
    },
    async ({ workflowId, text }, { client }) => {
      const raw = await client.post(`/workflows/${workflowId}/comment`, { text });
      return present(client, (presenter) => presenter.event(raw), { shouldLoadPeople: true });
    },
  ),

  tool(
    'update_workflow',
    {
      title: 'Update workflow',
      description:
        'Rename a workflow, change urgency, due date or kickoff field values. Only supplied kickoff fields change; ' +
        'a supplied file field replaces its files, so include the existing fileLinks to keep them. ' +
        'Pass dueDate null to clear it.',
      inputSchema: z.strictObject({
        workflowId,
        name: z.string().min(1).max(200).optional(),
        isUrgent: z.boolean().optional(),
        dueDate: dateTime.nullable().optional(),
        kickoff: fieldValues.optional(),
      }),
      annotations: idempotentUpdate,
    },
    async ({ workflowId, name, isUrgent, dueDate, kickoff }, { client }) => {
      let prepared = kickoff;
      if (kickoff) {
        const current = await client.get(`/workflows/${workflowId}`);
        const form = isRecord(current) && isRecord(current.kickoff) ? current.kickoff : {};
        prepared = prepareFieldValues(fieldSpecs(form.output, form.fieldsets), kickoff, { checkRequired: 'none' });
      }
      return workflowDetail(
        client,
        await client.patch(`/workflows/${workflowId}`, {
          name,
          is_urgent: isUrgent,
          kickoff: prepared,
          due_date_tsp: optionalTimestamp(dueDate),
        }),
      );
    },
  ),

  tool(
    'snooze_workflow',
    {
      title: 'Snooze workflow',
      description: 'Pause a running workflow until the given date; it resumes automatically.',
      inputSchema: z.strictObject({ workflowId, until: dateTime }),
      annotations: idempotentUpdate,
    },
    async ({ workflowId, until }, { client }) =>
      workflowDetail(client, await client.post(`/workflows/${workflowId}/snooze`, { date: toTimestamp(until) })),
  ),

  tool(
    'resume_workflow',
    {
      title: 'Resume workflow',
      description: 'Resume a snoozed workflow immediately.',
      inputSchema: z.strictObject({ workflowId }),
      annotations: idempotentUpdate,
    },
    async ({ workflowId }, { client }) => workflowDetail(client, await client.post(`/workflows/${workflowId}/resume`)),
  ),

  tool(
    'return_workflow_to_task',
    {
      title: 'Return workflow to task',
      description:
        'Move a workflow back to an earlier task step, which becomes active again; also reopens completed workflows. ' +
        'Identify the step by task ID or api_name.',
      inputSchema: z.strictObject({
        workflowId,
        taskId: id('Task').optional(),
        taskApiName: z.string().min(1).optional(),
      }),
      annotations: destructive,
    },
    async ({ workflowId, taskId, taskApiName }, { client }) => {
      if (!taskId && !taskApiName) {
        throw new ConnectorError('invalid_arguments', 'Provide taskId or taskApiName');
      }
      await client.post(`/workflows/${workflowId}/return-to`, { task: taskId, task_api_name: taskApiName });
      return successOutput();
    },
  ),

  tool(
    'finish_workflow',
    {
      title: 'Force-complete workflow',
      description:
        'Complete the whole workflow now, skipping remaining tasks. Allowed only for templates marked as finalizable.',
      inputSchema: z.strictObject({ workflowId }),
      annotations: destructive,
    },
    async ({ workflowId }, { client }) => {
      await client.post(`/workflows/${workflowId}/finish`);
      return successOutput();
    },
  ),

  tool(
    'terminate_workflow',
    {
      title: 'Terminate workflow',
      description: 'Permanently delete a workflow with all its tasks and history. This cannot be undone.',
      inputSchema: z.strictObject({ workflowId }),
      annotations: destructive,
    },
    async ({ workflowId }, { client }) => {
      await client.delete(`/workflows/${workflowId}`);
      return successOutput();
    },
  ),

  tool(
    'edit_comment',
    {
      title: 'Edit comment',
      description:
        'Change the text of a comment written by the connected user. The comment id is the event id from ' +
        'list_workflow_events or list_task_events (type comment). Only possible while its task is active or snoozed. ' +
        'The new text replaces the old one: keep existing "[name](url)" file links, omitted links detach their files.',
      inputSchema: z.strictObject({ commentId: id('Comment'), text: commentText }),
      annotations: idempotentUpdate,
    },
    async ({ commentId, text }, { client }) => {
      const raw = await client.patch(`/workflows/comments/${commentId}`, { text });
      return present(client, (presenter) => presenter.event(raw), { shouldLoadPeople: true });
    },
  ),

  tool(
    'delete_comment',
    {
      title: 'Delete comment',
      description: 'Delete a comment written by the connected user, including its attached files.',
      inputSchema: z.strictObject({ commentId: id('Comment') }),
      annotations: destructive,
    },
    async ({ commentId }, { client }) => {
      await client.delete(`/workflows/comments/${commentId}`);
      return successOutput();
    },
  ),

  tool(
    'react_to_comment',
    {
      title: 'React to comment',
      description:
        'Add (or with remove=true take back) a short reaction such as an emoji to a comment. The author is ' +
        'notified about new reactions.',
      inputSchema: z.strictObject({
        commentId: id('Comment'),
        reaction: z.string().min(1).max(10).describe('Emoji or short text, e.g. "👍"'),
        remove: z.boolean().default(false),
      }),
      annotations: idempotentUpdate,
    },
    async ({ commentId, reaction, remove }, { client }) => {
      await client.post(`/workflows/comments/${commentId}/${remove ? 'delete' : 'create'}-reaction`, {
        value: reaction,
      });
      return successOutput();
    },
  ),
];
