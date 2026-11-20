import * as z from 'zod/v4';

import { ConnectorError } from '../core/errors.js';
import { isRecord } from '../core/json.js';
import { tool, type ToolDef } from '../mcp/toolDef.js';
import { forgetPeople } from '../pneumatic/directory.js';
import { additive, destructive, idempotentUpdate, readOnly } from './annotations.js';
import { groupDetail, userDetail } from './details.js';
import { present, successOutput } from './output.js';
import { id, idList, requireExactlyOne } from './schemas.js';

const userId = id('User');
const groupId = id('Group');

export const peopleTools: ToolDef[] = [
  tool(
    'reassign_user',
    {
      title: 'Reassign user or group everywhere',
      description:
        'Replace a user or group with another one everywhere in the account (admins only): template step ' +
        'performers and owners, current task performers, workflow members and conditions. Use it before ' +
        'deactivating a user or for a permanent handover. Provide one source and one target.',
      inputSchema: z.strictObject({
        fromUserId: userId.optional(),
        fromGroupId: groupId.optional(),
        toUserId: userId.optional(),
        toGroupId: groupId.optional(),
      }),
      annotations: destructive,
    },
    async (args, { client }) => {
      requireExactlyOne(args, ['fromUserId', 'fromGroupId']);
      requireExactlyOne(args, ['toUserId', 'toGroupId']);
      await client.post('/accounts/users/reassign', {
        old_user: args.fromUserId,
        old_group: args.fromGroupId,
        new_user: args.toUserId,
        new_group: args.toGroupId,
      });
      return successOutput();
    },
  ),

  tool(
    'create_user',
    {
      title: 'Create user',
      description:
        'Add an active user to the account immediately (admins only). No invitation email is sent and the user ' +
        'gets a random password, so they sign in with password reset or SSO. Not an admin unless isAdmin=true. ' +
        'Repeating the call with the same email fails.',
      inputSchema: z.strictObject({
        email: z.email(),
        firstName: z.string().max(150).optional(),
        lastName: z.string().max(150).optional(),
        isAdmin: z.boolean().default(false),
        groupIds: idList('Group').optional(),
      }),
      annotations: additive,
    },
    async ({ email, firstName, lastName, isAdmin, groupIds }, { client }) =>
      userDetail(
        client,
        await client.post('/accounts/users', {
          email,
          first_name: firstName,
          last_name: lastName,
          is_admin: isAdmin,
          groups: groupIds,
        }),
      ),
  ),

  tool(
    'update_user',
    {
      title: 'Update user',
      description:
        'Change a user of the account (admins only): name, admin rights, groups, manager and subordinates. ' +
        'Only supplied values change; groupIds and subordinateIds replace the current lists.',
      inputSchema: z.strictObject({
        userId,
        firstName: z.string().max(150).optional(),
        lastName: z.string().max(150).optional(),
        isAdmin: z.boolean().optional(),
        groupIds: idList('Group').optional(),
        managerId: id('Manager user').nullable().optional(),
        subordinateIds: idList('User').optional(),
      }),
      annotations: idempotentUpdate,
    },
    async ({ userId, firstName, lastName, isAdmin, groupIds, managerId, subordinateIds }, { client }) => {
      return userDetail(
        client,
        await client.patch(`/accounts/users/${userId}`, {
          first_name: firstName,
          last_name: lastName,
          is_admin: isAdmin,
          groups: groupIds,
          manager_id: managerId,
          subordinates_ids: subordinateIds,
        }),
      );
    },
  ),

  tool(
    'get_assignment_count',
    {
      title: 'Count assignments of a user or group',
      description:
        'Count active templates where a user or group is an owner or step performer plus workflows where it ' +
        'performs tasks (admins only). Check it before deactivate_user or delete_group and hand over the work ' +
        'with reassign_user first.',
      inputSchema: z.strictObject({ userId: userId.optional(), groupId: groupId.optional() }),
      annotations: readOnly,
    },
    async (args, { client }) => {
      requireExactlyOne(args, ['userId', 'groupId']);
      const { userId, groupId } = args;
      const path = userId === undefined ? `/accounts/groups/${groupId}` : `/accounts/users/${userId}`;
      const raw = await client.get(`${path}/count-workflows`);
      return present(client, (presenter) => presenter.pick(raw, ['count']));
    },
  ),

  tool(
    'deactivate_user',
    {
      title: 'Deactivate user',
      description:
        'Deactivate a user (admins only): they can no longer sign in and their vacation and invites end. Fails ' +
        'while the user is the only performer of a task or step; call reassign_user first. The account owner ' +
        'and the connected user cannot be deactivated.',
      inputSchema: z.strictObject({ userId }),
      annotations: destructive,
    },
    async ({ userId }, { client }) => {
      await client.delete(`/accounts/users/${userId}`);
      forgetPeople(client);
      return successOutput();
    },
  ),

  tool(
    'create_group',
    {
      title: 'Create group',
      description: 'Create a user group (team) with members (admins only). Group names are unique in the account.',
      inputSchema: z.strictObject({ name: z.string().trim().min(1).max(255), userIds: idList('User').optional() }),
      annotations: additive,
    },
    async ({ name, userIds }, { client }) => {
      await client.post('/accounts/groups', { name, photo: '', users: userIds });
      // The create response echoes the input without the new ID.
      const groups = await client.get('/accounts/groups');
      const group = Array.isArray(groups)
        ? groups.find((item) => isRecord(item) && item.name === name && item.type !== 'personal')
        : undefined;
      return group ? groupDetail(client, group) : { data: { success: true, name } };
    },
  ),

  tool(
    'update_group',
    {
      title: 'Update group',
      description:
        'Rename a group or change its members (admins only). userIds replaces the member list; addUserIds and ' +
        'removeUserIds change it incrementally. Removed members lose tasks and templates assigned to the group.',
      inputSchema: z.strictObject({
        groupId,
        name: z.string().trim().min(1).max(255).optional(),
        userIds: idList('User').optional(),
        addUserIds: idList('User').optional(),
        removeUserIds: idList('User').optional(),
      }),
      annotations: destructive,
    },
    async ({ groupId, name, userIds, addUserIds = [], removeUserIds = [] }, { client }) => {
      const current = await client.get(`/accounts/groups/${groupId}`);
      if (!isRecord(current)) {
        throw new ConnectorError('invalid_response');
      }
      const members = new Set<number>(userIds ?? (Array.isArray(current.users) ? (current.users as number[]) : []));
      addUserIds.forEach((item) => members.add(item));
      removeUserIds.forEach((item) => members.delete(item));
      return groupDetail(
        client,
        await client.put(`/accounts/groups/${groupId}`, {
          name: name ?? current.name,
          photo: current.photo ?? '',
          users: [...members],
        }),
      );
    },
  ),

  tool(
    'delete_group',
    {
      title: 'Delete group',
      description: 'Delete a user group (admins only). Its members stay in the account.',
      inputSchema: z.strictObject({ groupId }),
      annotations: destructive,
    },
    async ({ groupId }, { client }) => {
      await client.delete(`/accounts/groups/${groupId}`);
      forgetPeople(client);
      return successOutput();
    },
  ),
];
