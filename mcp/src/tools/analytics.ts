import * as z from 'zod/v4';

import { ConnectorError } from '../core/errors.js';
import { isRecord } from '../core/json.js';
import { tool, type ToolDef } from '../mcp/toolDef.js';
import { localPage } from '../presenters/index.js';
import { readOnly } from './annotations.js';
import { periodQuery } from './dates.js';
import { present } from './output.js';
import { id, idList, limit, offset, period } from './schemas.js';

const STEP_STATS_KEYS = ['id', 'name', 'number', 'api_name', 'started', 'completed', 'in_progress', 'overdue'];

const COUNT_FILTERS = {
  starter: ['status', 'templateIds', 'currentPerformerIds', 'currentPerformerGroupIds'],
  performer: ['isExternal', 'templateIds', 'templateTaskApiNames', 'workflowStarterIds'],
  step: [
    'isExternal',
    'status',
    'templateIds',
    'workflowStarterIds',
    'currentPerformerIds',
    'currentPerformerGroupIds',
  ],
} as const;

const COUNT_PATHS = {
  starter: '/workflows/count/by-workflow-starter',
  performer: '/workflows/count/by-current-performer',
  step: '/workflows/count/by-template-task',
} as const;

export const analyticsTools: ToolDef[] = [
  tool(
    'get_workflow_field_values',
    {
      title: 'Get workflow field values',
      description:
        'Table of kickoff and task output values across workflows, newest first, with pagination (account owner ' +
        'only). Filter by template, status and field api names to answer questions such as "total amount of ' +
        'running contracts". Values are strings; date fields also carry an ISO date.',
      inputSchema: z.strictObject({
        templateId: id('Template').optional(),
        status: z.enum(['running', 'snoozed', 'done']).optional(),
        fieldApiNames: z.array(z.string().min(1).max(200)).min(1).max(50).optional().describe('Only these fields'),
        limit,
        offset,
      }),
      annotations: readOnly,
    },
    async ({ templateId, status, fieldApiNames, limit, offset }, { client }) => {
      const raw = await client.get('/workflows/fields', {
        template_id: templateId,
        status,
        fields: fieldApiNames,
        limit,
        offset,
      });
      return present(client, (presenter) =>
        presenter.page(raw, { limit, offset }, (item) => ({
          ...presenter.pick(item, ['id', 'name', 'date_created_tsp', 'date_completed_tsp']),
          status: presenter.workflowStatus(isRecord(item) ? item.status : undefined),
          fields: presenter.objects(isRecord(item) ? item.fields : undefined, (value) => ({
            ...presenter.fieldValue(value),
            ...presenter.pick(value, ['task_id']),
          })),
        })),
      );
    },
  ),

  tool(
    'get_template_step_stats',
    {
      title: 'Get template step statistics',
      description:
        'Started, completed, in-progress and overdue task counts per step of one template, to find where ' +
        'workflows get stuck. scope "all" counts all workflows of the template (template owners and viewers), ' +
        'scope "mine" only tasks assigned to the connected user. currentOnly=true returns a snapshot (in progress ' +
        'and overdue only).',
      inputSchema: z.strictObject({
        templateId: id('Template'),
        scope: z.enum(['all', 'mine']).default('all'),
        dateFrom: period.dateFrom,
        dateTo: period.dateTo,
        currentOnly: z.boolean().default(false),
      }),
      annotations: readOnly,
    },
    async ({ templateId, scope, dateFrom, dateTo, currentOnly }, { client }) => {
      const path = scope === 'all' ? '/reports/dashboard/workflows/by-tasks' : '/reports/dashboard/tasks/by-steps';
      const raw = await client.get(path, { template_id: templateId, ...periodQuery(dateFrom, dateTo, currentOnly) });
      return present(client, (presenter) =>
        presenter.objects(raw, (item) => presenter.pick(item, STEP_STATS_KEYS), 500),
      );
    },
  ),

  tool(
    'count_workflows',
    {
      title: 'Count workflows',
      description:
        'Count workflows visible to the connected user grouped by starter (sourceId -1 = external public-form ' +
        'workflows), by current performer (running workflows only) or by template step of templates the user ' +
        'owns. Performer filters work only with status "running". Not every filter applies to every grouping.',
      inputSchema: z.strictObject({
        groupBy: z.enum(['starter', 'performer', 'step']),
        status: z.enum(['running', 'snoozed', 'done']).optional(),
        templateIds: idList('Template').optional(),
        templateTaskApiNames: z.array(z.string().min(1).max(200)).optional(),
        workflowStarterIds: idList('User').optional(),
        currentPerformerIds: idList('User').optional(),
        currentPerformerGroupIds: idList('Group').optional(),
        isExternal: z.boolean().optional(),
        limit,
        offset,
      }),
      annotations: readOnly,
    },
    async ({ groupBy, limit, offset, ...filters }, { client }) => {
      const allowed: readonly string[] = COUNT_FILTERS[groupBy];
      const unsupported = Object.keys(filters).filter(
        (key) => filters[key as keyof typeof filters] !== undefined && !allowed.includes(key),
      );
      if (unsupported.length) {
        throw new ConnectorError(
          'invalid_arguments',
          `groupBy "${groupBy}" does not support: ${unsupported.join(', ')}`,
        );
      }
      const raw = await client.get(COUNT_PATHS[groupBy], {
        status: filters.status,
        template_ids: filters.templateIds,
        template_task_api_names: filters.templateTaskApiNames,
        workflow_starter_ids: filters.workflowStarterIds,
        current_performer_ids: filters.currentPerformerIds,
        current_performer_group_ids: filters.currentPerformerGroupIds,
        is_external: filters.isExternal,
      });
      return present(client, (presenter) =>
        presenter.page(localPage(raw, { limit, offset }), { limit, offset }, (item) =>
          presenter.pick(item, ['type', 'source_id', 'template_task_api_name', 'workflows_count']),
        ),
      );
    },
  ),
];
