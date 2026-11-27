import * as z from 'zod/v4';

import { tool, type ToolDef } from '../mcp/toolDef.js';
import { localPage } from '../presenters/index.js';
import { readOnly } from './annotations.js';
import { optionalTimestamp, periodQuery } from './dates.js';
import { present } from './output.js';
import { dateTime, idList, limit, offset, period } from './schemas.js';

export const reportTools: ToolDef[] = [
  tool(
    'get_dashboard',
    {
      title: 'Get dashboard',
      description:
        'Get process KPIs for a period: started, completed, in progress and overdue counts. ' +
        'scope "workflows" counts workflows, scope "tasks" counts tasks; both are limited to what the current user can access. ' +
        'breakdown "template" splits the numbers by template.',
      inputSchema: z.strictObject({
        scope: z.enum(['workflows', 'tasks']),
        breakdown: z.enum(['none', 'template']).default('none'),
        ...period,
        limit,
        offset,
      }),
      annotations: readOnly,
    },
    async ({ scope, breakdown, dateFrom, dateTo, currentOnly, limit, offset }, { client }) => {
      const query = periodQuery(dateFrom, dateTo, currentOnly);
      if (breakdown === 'template') {
        const raw = localPage(await client.get(`/reports/dashboard/${scope}/breakdown`, query), { limit, offset });
        return present(client, (presenter) =>
          presenter.page(raw, { limit, offset }, (item) =>
            presenter.pick(item, [
              'template_id',
              'template_name',
              'is_active',
              'started',
              'completed',
              'in_progress',
              'overdue',
            ]),
          ),
        );
      }
      const raw = await client.get(`/reports/dashboard/${scope}/overview`, query);
      return present(client, (presenter) => presenter.pick(raw, ['started', 'completed', 'in_progress', 'overdue']));
    },
  ),

  tool(
    'list_highlights',
    {
      title: 'List activity highlights',
      description:
        'Account-wide activity feed across workflows (task completions, returns, comments, snoozes). ' +
        'Useful for status reports like "what happened this week".',
      inputSchema: z.strictObject({
        dateFrom: dateTime.optional(),
        dateTo: dateTime.optional(),
        templateIds: idList('Template').optional(),
        performerIds: idList('User').optional(),
        performerGroupIds: idList('Group').optional(),
        limit,
        offset,
      }),
      annotations: readOnly,
    },
    async (args, { client }) => {
      const raw = await client.get('/reports/highlights', {
        date_after_tsp: optionalTimestamp(args.dateFrom),
        date_before_tsp: optionalTimestamp(args.dateTo),
        templates: args.templateIds,
        current_performer_ids: args.performerIds,
        current_performer_group_ids: args.performerGroupIds,
        limit: args.limit,
        offset: args.offset,
      });
      return present(client, (presenter) => presenter.page(raw, args, (item) => presenter.highlight(item)), {
        shouldLoadPeople: true,
      });
    },
  ),
];
