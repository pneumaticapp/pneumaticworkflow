import * as z from 'zod/v4';

import { ConnectorError } from '../core/errors.js';
import { isRecord, records } from '../core/json.js';
import { tool, type ToolDef } from '../mcp/toolDef.js';
import type { PneumaticClient } from '../pneumatic/client.js';
import { additive, destructive, idempotentUpdate } from './annotations.js';
import { templateDetail } from './details.js';
import { successOutput } from './output.js';
import { id } from './schemas.js';
import {
  appendFields,
  checklistPayload,
  dueDatePayload,
  field,
  fieldPayload,
  performer,
  performerPayload,
  step,
  taskPayload,
} from './templatePayload.js';
import {
  assertUnreferenced,
  chainInOrder,
  fieldApiNamesOf,
  newTaskApiName,
  renumber,
  replaceStartRule,
  rewireSuccessors,
  sortedTasks,
  type RawTask,
  startCondition,
  startRuleAfter,
  startsRightAfter,
  usesStartRules,
} from './templateSteps.js';
import { fetchTemplate } from './templates.js';

const templateId = id('Template');

async function currentUserId(client: PneumaticClient): Promise<number> {
  const user = await client.get('/accounts/user');
  if (!isRecord(user) || typeof user.id !== 'number') {
    throw new ConnectorError('invalid_response');
  }
  return user.id;
}

function assignDefined(target: Record<string, unknown>, changes: Record<string, unknown>) {
  for (const [key, value] of Object.entries(changes)) {
    if (value !== undefined) {
      target[key] = value;
    }
  }
}

function stepOf(template: Record<string, unknown>, stepApiName: string): RawTask {
  const task = sortedTasks(template).find((item) => item.api_name === stepApiName);
  if (!task) {
    throw new ConnectorError('invalid_arguments', `The template has no step "${stepApiName}"`);
  }
  return task;
}

// PUT replaces the whole template, so the current definition is sent back with only the requested changes.
async function editTemplate(
  client: PneumaticClient,
  templateId: number,
  change: (template: Record<string, unknown>) => void,
) {
  const template = structuredClone(await fetchTemplate(client, templateId));
  change(template);
  return templateDetail(client, await client.put(`/templates/${templateId}`, template));
}

export const designerTools: ToolDef[] = [
  tool(
    'create_template',
    {
      title: 'Create workflow template',
      description:
        'Design a new process template (admins only): kickoff form fields and ordered steps with performers, ' +
        'output fields, checklists and due dates. Steps run one after another by default (sequential=false starts ' +
        'them all at once). The connected user becomes the template owner and the default performer. With ' +
        'isActive=false the template is saved as a draft. Returns the created template; use get_template_kickoff ' +
        'and run_workflow to launch it. Repeating the call creates another template.',
      inputSchema: z.strictObject({
        name: z.string().trim().min(1).max(120),
        description: z.string().max(5000).optional(),
        kickoffFields: z.array(field).max(50).optional().describe('Fields filled in when a workflow is started'),
        steps: z.array(step).min(1).max(100),
        sequential: z.boolean().default(true),
        isActive: z.boolean().default(true).describe('false = save as an inactive draft'),
        finalizable: z.boolean().optional().describe('Allow finishing workflows early (finish_workflow)'),
      }),
      annotations: additive,
    },
    async (args, { client }) => {
      const userId = await currentUserId(client);
      const tasks = args.steps.map((item, index) => ({
        number: index + 1,
        ...taskPayload(item, newTaskApiName(), userId),
        conditions: [],
      }));
      if (args.sequential) {
        chainInOrder(tasks);
      }
      const raw = await client.post('/templates', {
        name: args.name,
        description: args.description ?? '',
        is_active: args.isActive,
        ...(args.finalizable === undefined ? {} : { finalizable: args.finalizable }),
        owners: [{ type: 'user', source_id: String(userId), role: 'owner' }],
        kickoff: { fields: fieldPayload(args.kickoffFields) },
        tasks,
      });
      return templateDetail(client, raw);
    },
  ),

  tool(
    'update_template',
    {
      title: 'Update template settings',
      description:
        'Rename a template, change its description or naming rule, allow early finishing, publish it as a public ' +
        'or embeddable form (data.publicUrl / data.embedUrl), or activate / deactivate it (isActive=false keeps it ' +
        'as a draft and stops new launches). Use the *_template_step and update_template_kickoff tools for steps ' +
        'and fields. Activating a draft validates the whole template. Changes to an active template are applied ' +
        'to its running workflows.',
      inputSchema: z.strictObject({
        templateId,
        name: z.string().trim().min(1).max(120).optional(),
        description: z.string().max(5000).optional(),
        isActive: z.boolean().optional(),
        finalizable: z.boolean().optional(),
        isPublic: z.boolean().optional().describe('Anyone with the public link can start a workflow'),
        isEmbedded: z.boolean().optional().describe('The kickoff form can be embedded on a website'),
        workflowNameTemplate: z
          .string()
          .max(500)
          .nullable()
          .optional()
          .describe('Workflow naming rule, e.g. "{{template-name}} {{date}}" or with {{kickoff_field_api_name}}'),
      }),
      annotations: idempotentUpdate,
    },
    async (args, { client }) =>
      editTemplate(client, args.templateId, (template) =>
        assignDefined(template, {
          name: args.name,
          description: args.description,
          finalizable: args.finalizable,
          is_active: args.isActive,
          is_public: args.isPublic,
          is_embedded: args.isEmbedded,
          wf_name_template: args.workflowNameTemplate,
        }),
      ),
  ),

  tool(
    'add_template_step',
    {
      title: 'Add template step',
      description:
        'Insert a step into a template at a position (1 = first; default last) with the same options as ' +
        'create_template steps. In a template whose steps run one after another, the new step is chained after ' +
        'the previous one and the following step now waits for it. Running workflows pick up the change.',
      inputSchema: z.strictObject({
        templateId,
        step,
        position: z.number().int().min(1).optional().describe('Step number of the new step'),
      }),
      annotations: additive,
    },
    async ({ templateId, step: input, position }, { client }) => {
      const userId = await currentUserId(client);
      return editTemplate(client, templateId, (template) => {
        const tasks = sortedTasks(template);
        const index = Math.min(Math.max((position ?? tasks.length + 1) - 1, 0), tasks.length);
        const previous = tasks[index - 1];
        const next = tasks[index];
        const added = taskPayload(input, newTaskApiName(), userId);
        added.conditions = usesStartRules(tasks) ? [startCondition(startRuleAfter(previous))] : [];
        if (next && startsRightAfter(next, previous)) {
          replaceStartRule(next, { after: 'step', apiName: added.api_name });
        }
        tasks.splice(index, 0, added);
        template.tasks = renumber(tasks);
      });
    },
  ),

  tool(
    'update_template_step',
    {
      title: 'Update template step',
      description:
        'Change one template step identified by its apiName (from get_template): name, description, performers ' +
        '(replaced), checklist (replaced; [] removes), due date (dueInHours; null removes), completion by all ' +
        'performers, and new output fields (addFields). Remove fields with remove_template_fields. Other steps ' +
        'are unchanged.',
      inputSchema: z.strictObject({
        templateId,
        stepApiName: z.string().min(1).max(200),
        name: z.string().trim().min(1).max(280).optional(),
        description: z.string().max(5000).optional(),
        performers: z.array(performer).min(1).max(50).optional(),
        checklist: z.array(z.string().trim().min(1).max(2000)).max(100).optional(),
        dueInHours: z
          .number()
          .positive()
          .max(24 * 365)
          .nullable()
          .optional(),
        requireCompletionByAll: z.boolean().optional(),
        addFields: z.array(field).max(50).optional(),
      }),
      annotations: idempotentUpdate,
    },
    async (args, { client }) =>
      editTemplate(client, args.templateId, (template) => {
        const task = stepOf(template, args.stepApiName);
        assignDefined(task, {
          name: args.name,
          description: args.description,
          require_completion_by_all: args.requireCompletionByAll,
        });
        if (args.performers) {
          task.raw_performers = performerPayload(args.performers);
        }
        if (args.checklist) {
          task.checklists = checklistPayload(args.checklist);
        }
        if (args.dueInHours !== undefined) {
          task.raw_due_date = args.dueInHours === null ? null : dueDatePayload(args.dueInHours, String(task.api_name));
        }
        task.fields = appendFields(task.fields, args.addFields, task.fieldsets);
      }),
  ),

  tool(
    'remove_template_step',
    {
      title: 'Remove template step',
      description:
        "Delete a template step by apiName. A step that started after it now starts after the removed step's " +
        'predecessor. Refused while other steps, conditions, due dates, revert targets or texts still refer to the ' +
        'step. Running workflows pick up the change.',
      inputSchema: z.strictObject({ templateId, stepApiName: z.string().min(1).max(200) }),
      annotations: destructive,
    },
    async ({ templateId, stepApiName }, { client }) =>
      editTemplate(client, templateId, (template) => {
        const tasks = sortedTasks(template);
        const index = tasks.findIndex((task) => task.api_name === stepApiName);
        const removed = tasks[index];
        if (!removed) {
          throw new ConnectorError('invalid_arguments', `The template has no step "${stepApiName}"`);
        }
        if (tasks.length === 1) {
          throw new ConnectorError('invalid_arguments', 'A template needs at least one step');
        }
        rewireSuccessors(tasks, removed);
        tasks.splice(index, 1);
        template.tasks = renumber(tasks);
        // Fields of the removed step disappear with it, so nothing may refer to them either.
        assertUnreferenced(template, [stepApiName], 'step');
        assertUnreferenced(template, fieldApiNamesOf(removed), 'field');
      }),
  ),

  tool(
    'remove_template_fields',
    {
      title: 'Remove template fields',
      description:
        'Delete fields from a step (stepApiName) or from the kickoff form (stepApiName omitted). Running workflows ' +
        'of an active template lose these fields and their values. Refused while conditions, names, due dates or ' +
        'performers still refer to a field.',
      inputSchema: z.strictObject({
        templateId,
        stepApiName: z.string().min(1).max(200).optional(),
        fieldApiNames: z.array(z.string().min(1).max(200)).min(1).max(50),
      }),
      annotations: destructive,
    },
    async ({ templateId, stepApiName, fieldApiNames }, { client }) =>
      editTemplate(client, templateId, (template) => {
        const owner =
          stepApiName === undefined
            ? isRecord(template.kickoff)
              ? template.kickoff
              : undefined
            : sortedTasks(template).find((task) => task.api_name === stepApiName);
        if (!owner) {
          throw new ConnectorError('invalid_arguments', `The template has no step "${stepApiName}"`);
        }
        const fields = records(owner.fields);
        const unknown = fieldApiNames.filter((name) => !fields.some((item) => item.api_name === name));
        if (unknown.length) {
          throw new ConnectorError('invalid_arguments', `Unknown field api names: ${unknown.join(', ')}`);
        }
        owner.fields = fields.filter((item) => !fieldApiNames.includes(String(item.api_name)));
        assertUnreferenced(template, fieldApiNames, 'field');
      }),
  ),

  tool(
    'update_template_kickoff',
    {
      title: 'Add kickoff form fields',
      description:
        'Add fields to the kickoff form of a template (filled in when a workflow starts). Existing fields keep ' +
        'their api names and order. Remove fields with remove_template_fields.',
      inputSchema: z.strictObject({ templateId, addFields: z.array(field).min(1).max(50) }),
      annotations: idempotentUpdate,
    },
    async ({ templateId, addFields }, { client }) =>
      editTemplate(client, templateId, (template) => {
        const kickoff = isRecord(template.kickoff) ? template.kickoff : {};
        kickoff.fields = appendFields(kickoff.fields, addFields, kickoff.fieldsets);
        template.kickoff = kickoff;
      }),
  ),

  tool(
    'clone_template',
    {
      title: 'Clone template',
      description:
        'Copy a template (including unsaved draft edits) into a new inactive draft named "<name> - clone". ' +
        'Activate it with update_template isActive=true.',
      inputSchema: z.strictObject({ templateId }),
      annotations: additive,
    },
    async ({ templateId }, { client }) => templateDetail(client, await client.post(`/templates/${templateId}/clone`)),
  ),

  tool(
    'delete_template',
    {
      title: 'Delete template',
      description:
        'Delete a template. Running workflows are not terminated: they continue as legacy workflows without ' +
        'template updates. This cannot be undone from the connector.',
      inputSchema: z.strictObject({ templateId }),
      annotations: destructive,
    },
    async ({ templateId }, { client }) => {
      await client.delete(`/templates/${templateId}`);
      return successOutput();
    },
  ),
];
