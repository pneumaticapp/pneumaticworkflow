import * as z from 'zod/v4';

import { ConnectorError } from '../core/errors.js';
import { isRecord, records } from '../core/json.js';
import { tool, type ToolDef } from '../mcp/toolDef.js';
import type { PneumaticClient } from '../pneumatic/client.js';
import { pageResults } from '../presenters/index.js';
import { additive, readOnly } from './annotations.js';
import { optionalTimestamp } from './dates.js';
import { templateDetail, workflowDetail } from './details.js';
import { fieldSpecs, prepareFieldValues } from './fields.js';
import { present } from './output.js';
import { dateTime, fieldValues, id, limit, offset } from './schemas.js';

const KICKOFF_PAGE_SIZE = 100;
const MAX_KICKOFF_PAGES = 20;

export async function fetchTemplate(client: PneumaticClient, templateId: number): Promise<Record<string, unknown>> {
  const raw = await client.get(`/templates/${templateId}`);
  if (raw === null) {
    throw new ConnectorError('not_found', 'The template is inactive and has no saved draft');
  }
  if (!isRecord(raw)) {
    throw new ConnectorError('invalid_response');
  }
  return raw;
}

// The template list honours starter/viewer access and embeds the kickoff form, unlike GET /templates/{id}.
async function findTemplate(client: PneumaticClient, templateId: number) {
  for (let page = 0; page < MAX_KICKOFF_PAGES; page += 1) {
    const raw = await client.get('/templates', { limit: KICKOFF_PAGE_SIZE, offset: page * KICKOFF_PAGE_SIZE });
    const results = pageResults(raw);
    const template = records(results).find((item) => item.id === templateId);
    if (template) {
      return template;
    }
    if (results.length < KICKOFF_PAGE_SIZE) {
      break;
    }
  }
  throw new ConnectorError(
    'not_found',
    `Template ${templateId} is not among the templates the connected user can access`,
  );
}

// Admins also reach templates beyond the listed pages through the detail; without access Pneumatic validates itself.
async function kickoffSource(client: PneumaticClient, templateId: number) {
  try {
    return await findTemplate(client, templateId);
  } catch (error) {
    if (!(error instanceof ConnectorError && error.code === 'not_found')) {
      throw error;
    }
  }
  const detail = await client.get(`/templates/${templateId}`).catch(() => undefined);
  return isRecord(detail) ? detail : undefined;
}

export const templateTools: ToolDef[] = [
  tool(
    'list_templates',
    {
      title: 'List workflow templates',
      description:
        'List template summaries visible to the connected user with pagination. A workflow is always started ' +
        'from a template. Check isActive before starting a workflow; use get_template_kickoff to read its launch fields.',
      inputSchema: z.strictObject({
        search: z.string().max(200).optional().describe('Search by template name'),
        isActive: z.boolean().optional().describe('true = only active templates that can be run'),
        ordering: z
          .enum(['name', '-name', 'date', '-date', 'usage', '-usage'])
          .optional()
          .describe('Sort order; prefix "-" means descending'),
        limit,
        offset,
      }),
      annotations: readOnly,
    },
    async ({ search, isActive, ordering, limit, offset }, { client }) => {
      const raw = await client.get('/templates', { search, is_active: isActive, ordering, limit, offset });
      return present(client, (presenter) => presenter.page(raw, { limit, offset }, (item) => presenter.template(item)));
    },
  ),

  tool(
    'get_template',
    {
      title: 'Get workflow template',
      description:
        'Get the template definition: kickoff fields, ordered task steps with their fields, performers, checklists, ' +
        'conditions and due-date rules. Requires the account owner or an admin who owns the template; to prepare ' +
        'a launch with starter/viewer access use get_template_kickoff instead. Template steps are not workflow ' +
        'task instances and cannot be passed to complete_task.',
      inputSchema: z.strictObject({ templateId: id('Template') }),
      annotations: readOnly,
    },
    async ({ templateId }, { client }) => templateDetail(client, await fetchTemplate(client, templateId)),
  ),

  tool(
    'get_template_kickoff',
    {
      title: 'Get template kickoff form',
      description:
        'Get the kickoff form of a template under template-access permissions (owners, viewers and starters), ' +
        'without requiring template edit rights. Inspect data.fields and data.fieldsets[].fields for api names, ' +
        'types, required/hidden flags and selections before run_workflow. Reading the form does not launch ' +
        'a workflow; check data.isActive.',
      inputSchema: z.strictObject({ templateId: id('Template') }),
      annotations: readOnly,
    },
    async ({ templateId }, { client }) => {
      const template = await findTemplate(client, templateId);
      return present(client, (presenter) => ({
        templateId,
        ...presenter.pick(template, ['name', 'description', 'is_active'], ['description']),
        ...presenter.kickoffDefinition(template.kickoff),
      }));
    },
  ),

  tool(
    'run_workflow',
    {
      title: 'Run workflow',
      description:
        'Create and start a new workflow from an active template. Read get_template_kickoff first and supply ' +
        'required kickoff fields by api_name; schema defaults are not applied to omitted fields. Returns the new ' +
        'workflow with its tasks. May notify people or trigger integrations. Repeating the call creates another ' +
        'workflow; after an uncertain result check list_workflows before retrying.',
      inputSchema: z.strictObject({
        templateId: id('Template'),
        name: z.string().min(1).max(200).optional().describe('Workflow name; defaults to the template naming rule'),
        kickoff: fieldValues.optional(),
        isUrgent: z.boolean().optional(),
        dueDate: dateTime.optional().describe('Workflow due date (ISO 8601 or Unix seconds)'),
        ancestorTaskId: id('Task').optional().describe('Run as a sub-workflow of this task'),
      }),
      annotations: additive,
    },
    async ({ templateId, name, kickoff, isUrgent, dueDate, ancestorTaskId }, { client }) => {
      const template = await kickoffSource(client, templateId);
      const form = template && isRecord(template.kickoff) ? template.kickoff : undefined;
      const prepared = form
        ? prepareFieldValues(fieldSpecs(form.fields, form.fieldsets), kickoff, { checkRequired: 'all' })
        : kickoff;
      const raw = await client.post(`/templates/${templateId}/run`, {
        name,
        kickoff: prepared,
        is_urgent: isUrgent,
        due_date_tsp: optionalTimestamp(dueDate),
        ancestor_task_id: ancestorTaskId,
      });
      return workflowDetail(client, raw);
    },
  ),
];
