import * as z from 'zod/v4';

import { ConnectorError } from '../core/errors.js';
import { isRecord } from '../core/json.js';
import { tool, type ToolDef } from '../mcp/toolDef.js';
import { localPage } from '../presenters/index.js';
import { idempotentUpdate, readOnly } from './annotations.js';
import { userDetail } from './details.js';
import { present, successOutput } from './output.js';
import { id, idList, limit, offset } from './schemas.js';

const isoDate = z.iso.date().describe('Date as YYYY-MM-DD');

export const accountTools: ToolDef[] = [
  tool(
    'get_current_user',
    {
      title: 'Get current user',
      description:
        'Get the Pneumatic user the connector acts as (the API key owner): id, name, email, admin flags, ' +
        'timezone, language, group IDs and absence status.',
      inputSchema: z.strictObject({}),
      annotations: readOnly,
    },
    async (_args, { client }) => {
      const raw = await client.get('/accounts/user');
      return present(client, (presenter) => presenter.user(raw, { isDetailed: true }));
    },
  ),

  tool(
    'list_users',
    {
      title: 'List users',
      description:
        'List users of the Pneumatic account with pagination. Use it to resolve a person name or email into a ' +
        'user ID for assigning performers or filtering workflows and tasks. User fields in kickoff/output take ' +
        'the email instead of the ID.',
      inputSchema: z.strictObject({
        status: z.enum(['active', 'inactive', 'invited']).optional().describe('Filter by user status'),
        type: z.enum(['user', 'guest']).optional().describe('Filter by user type'),
        groupIds: idList('Group').optional().describe('Only users that belong to these groups'),
        limit,
        offset,
      }),
      annotations: readOnly,
    },
    async ({ status, type, groupIds, limit, offset }, { client }) => {
      const raw = await client.get('/accounts/users', { status, type, groups: groupIds, limit, offset });
      return present(client, (presenter) => presenter.page(raw, { limit, offset }, (item) => presenter.user(item)));
    },
  ),

  tool(
    'list_groups',
    {
      title: 'List groups',
      description:
        'List user groups (teams) of the Pneumatic account with their member user IDs. ' +
        'Group fields in kickoff/output take the group name.',
      inputSchema: z.strictObject({ limit, offset }),
      annotations: readOnly,
    },
    async ({ limit, offset = 0 }, { client }) => {
      const raw = localPage(await client.get('/accounts/groups'), { limit, offset });
      return present(client, (presenter) => presenter.page(raw, { limit, offset }, (item) => presenter.group(item)));
    },
  ),

  tool(
    'set_vacation',
    {
      title: 'Set vacation or sick leave',
      description:
        'Start or update (active=true) or end (active=false) a vacation or sick leave. While it is active, the ' +
        "user's tasks are delegated to the substitutes, who are notified. Omit userId for the connected user; " +
        "another user's absence needs an admin. It starts immediately and ends automatically the day after endDate.",
      inputSchema: z.strictObject({
        userId: id('User').optional(),
        active: z.boolean(),
        substituteUserIds: idList('Substitute user').min(1).optional().describe('Required when active=true'),
        startDate: isoDate.optional(),
        endDate: isoDate.optional(),
        absenceStatus: z.enum(['vacation', 'sick_leave']).default('vacation'),
      }),
      annotations: idempotentUpdate,
    },
    async ({ userId, active, substituteUserIds, startDate, endDate, absenceStatus }, { client }) => {
      const base = userId === undefined ? '/accounts/user' : `/accounts/users/${userId}`;
      if (!active) {
        return userDetail(client, await client.post(`${base}/deactivate-vacation`));
      }
      if (!substituteUserIds) {
        throw new ConnectorError('invalid_arguments', 'substituteUserIds is required to start a vacation');
      }
      return userDetail(
        client,
        await client.post(`${base}/activate-vacation`, {
          substitute_user_ids: substituteUserIds,
          vacation_start_date: startDate,
          vacation_end_date: endDate,
          absence_status: absenceStatus,
        }),
      );
    },
  ),

  tool(
    'list_notifications',
    {
      title: 'List notifications',
      description:
        "List the connected user's in-app notifications, newest first, with pagination: comments, mentions, " +
        'reactions, overdue and due-date changes, snoozed/resumed and completed workflows. Also returns ' +
        'activeTaskCount, the number of tasks waiting for the user.',
      inputSchema: z.strictObject({ status: z.enum(['new', 'read']).optional(), limit, offset }),
      annotations: readOnly,
    },
    async ({ status, limit, offset }, { client }) => {
      const [raw, counters] = await Promise.all([
        client.get('/accounts/notifications', { status, limit, offset }),
        client.get('/accounts/user/counters'),
      ]);
      return present(
        client,
        (presenter) => ({
          ...presenter.page(raw, { limit, offset }, (item) => ({
            ...presenter.pick(item, ['id', 'type', 'status', 'text', 'datetime_tsp', 'author'], ['text']),
            authorName: presenter.userName(isRecord(item) ? item.author : undefined),
            task:
              isRecord(item) && isRecord(item.task) ? presenter.pick(item.task, ['id', 'name', 'due_date_tsp']) : null,
            workflow: isRecord(item) && isRecord(item.workflow) ? presenter.pick(item.workflow, ['id', 'name']) : null,
          })),
          activeTaskCount: isRecord(counters) ? presenter.value(counters.tasks_count) : null,
        }),
        { shouldLoadPeople: true },
      );
    },
  ),

  tool(
    'mark_notifications_read',
    {
      title: 'Mark notifications read',
      description: 'Mark notifications of the connected user as read.',
      inputSchema: z.strictObject({ notificationIds: idList('Notification').min(1).max(500) }),
      annotations: idempotentUpdate,
    },
    async ({ notificationIds }, { client }) => {
      await client.post('/accounts/notifications/read', { notifications: notificationIds });
      return successOutput();
    },
  ),
];
