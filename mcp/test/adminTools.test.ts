import type { Client } from '@modelcontextprotocol/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { formatDuration } from '../src/tools/templatePayload.js';
import { createFakePneumatic } from './fakePneumatic.js';
import { callTool, connectServer, lastBody } from './harness.js';

let fake: ReturnType<typeof createFakePneumatic>;
let client: Client;

const call = (name: string, args?: Record<string, unknown>) => callTool(client, name, args);
const body = (path: string, method?: string) => lastBody(fake, path, method);

beforeEach(async () => {
  fake = createFakePneumatic();
  client = await connectServer(fake);
});

afterEach(async () => {
  await client.close();
});

describe('template design', () => {
  it('creates an active template whose steps run one after another', async () => {
    const result = await call('create_template', {
      name: 'Onboarding',
      kickoffFields: [
        { name: 'Employee', type: 'user' },
        { name: 'Team', type: 'dropdown', selections: ['Sales', 'Ops'] },
      ],
      steps: [
        { name: 'Prepare laptop', checklist: ['Order', 'Install'], dueInHours: 30 },
        { name: 'Intro call', performers: [{ type: 'group', id: 4 }, { type: 'workflowStarter' }] },
      ],
    });
    expect(result.isError).toBe(false);
    const payload = body('/templates', 'POST');
    expect(payload).toMatchObject({
      name: 'Onboarding',
      is_active: true,
      owners: [{ type: 'user', source_id: '7', role: 'owner' }],
      kickoff: {
        fields: [
          { name: 'Employee', type: 'user', is_required: true, order: 2 },
          { name: 'Team', type: 'dropdown', order: 1, selections: [{ value: 'Sales' }, { value: 'Ops' }] },
        ],
      },
    });
    const [first, second] = payload.tasks;
    expect(first).toMatchObject({
      number: 1,
      raw_performers: [{ type: 'user', source_id: 7 }],
      checklists: [{ selections: [{ value: 'Order' }, { value: 'Install' }] }],
      raw_due_date: { duration: '1 06:00:00', rule: 'after task started', source_id: expect.stringMatching(/^task-/) },
      conditions: [
        { action: 'start_task', rules: [{ predicates: [{ field_type: 'kickoff', operator: 'completed' }] }] },
      ],
    });
    expect(first.raw_due_date.source_id).toBe(first.api_name);
    expect(second.raw_performers).toEqual([
      { type: 'group', source_id: 4 },
      { type: 'workflow_starter', source_id: null },
    ]);
    expect(second.conditions[0].rules[0].predicates[0]).toEqual({
      field_type: 'task',
      operator: 'completed',
      field: first.api_name,
      value: null,
    });
  });

  it('runs steps in parallel on request and validates options before calling the API', async () => {
    await call('create_template', { name: 'Parallel', sequential: false, steps: [{ name: 'A' }, { name: 'B' }] });
    expect(body('/templates', 'POST').tasks.map((task: any) => task.conditions)).toEqual([[], []]);

    const invalid = await call('create_template', {
      name: 'Bad',
      steps: [{ name: 'A', fields: [{ name: 'Choice', type: 'radio' }] }],
    });
    expect(invalid.error).toMatchObject({ code: 'invalid_arguments', detail: expect.stringContaining('selections') });
  });

  it('formats due-date durations for Pneumatic', () => {
    expect(formatDuration(1.5)).toBe('01:30:00');
    expect(formatDuration(48)).toBe('2 00:00:00');
    expect(formatDuration(0.001)).toBe('00:01:00');
  });

  it('updates template settings by sending back the full definition', async () => {
    const current = { id: 4, name: 'Old', description: 'Keep', is_active: true, tasks: [{ api_name: 'task-1' }] };
    fake.respond((request) =>
      request.path === '/templates/4' && request.method === 'GET' ? { body: current } : undefined,
    );
    await call('update_template', { templateId: 4, name: 'New', isActive: false });
    expect(body('/templates/4', 'PUT')).toEqual({ ...current, name: 'New', is_active: false });
  });

  it('chains library steps and keeps the new template as a draft', async () => {
    fake.respond((request) =>
      request.path === '/templates/system/3/fill'
        ? {
            body: {
              name: 'Hiring',
              tasks: [
                { number: 2, name: 'B', api_name: 'task-b' },
                { number: 1, name: 'A' },
              ],
            },
          }
        : undefined,
    );
    await call('create_template_from_library', { libraryTemplateId: 3 });
    const payload = body('/templates', 'POST');
    expect(payload.is_active).toBe(false);
    const [second, first] = payload.tasks;
    expect(first.conditions[0].rules[0].predicates[0].field_type).toBe('kickoff');
    expect(second.conditions[0].rules[0].predicates[0].field).toBe(first.api_name);
  });

  it('returns AI-proposed steps without creating a template', async () => {
    fake.respond((request) =>
      request.path === '/templates/ai'
        ? { body: { name: 'Audit', tasks: [{ number: 1, name: 'Plan', description: 'Scope', raw_performers: [] }] } }
        : undefined,
    );
    const { data } = await call('generate_template_steps', { description: 'Internal audit' });
    expect(data).toEqual({ name: 'Audit', steps: [{ number: 1, name: 'Plan', description: 'Scope' }] });
    expect(body('/templates', 'POST')).toBeUndefined();
  });
});

describe('analytics', () => {
  it('queries field values and names workflow statuses', async () => {
    fake.respond((request) =>
      request.path === '/workflows/fields'
        ? {
            body: {
              count: 1,
              results: [{ id: 1, name: 'Deal', status: 0, fields: [{ api_name: 'amount', value: '10' }] }],
            },
          }
        : undefined,
    );
    const { data } = await call('get_workflow_field_values', { templateId: 2, fieldApiNames: ['amount', 'client'] });
    expect(fake.lastRequest('/workflows/fields')?.query).toEqual({
      template_id: '2',
      fields: 'amount,client',
      limit: '20',
    });
    expect(data.items[0]).toMatchObject({ status: 'running', fields: [{ apiName: 'amount', value: '10' }] });
  });

  it('picks the step statistics endpoint by scope', async () => {
    await call('get_template_step_stats', { templateId: 5, scope: 'mine', currentOnly: true });
    expect(fake.lastRequest('/reports/dashboard/tasks/by-steps')?.query).toEqual({ template_id: '5', now: 'true' });
  });

  it('rejects filters that a workflow count grouping does not support', async () => {
    const result = await call('count_workflows', { groupBy: 'performer', status: 'done' });
    expect(result.error).toMatchObject({ code: 'invalid_arguments', detail: expect.stringContaining('status') });
    await call('count_workflows', { groupBy: 'starter', templateIds: [1, 2] });
    expect(fake.lastRequest('/workflows/count/by-workflow-starter')?.query).toEqual({ template_ids: '1,2' });
  });
});

describe('people', () => {
  it('starts and ends vacations for the current or another user', async () => {
    await call('set_vacation', { active: true, substituteUserIds: [3], endDate: '2026-11-01' });
    expect(body('/accounts/user/activate-vacation')).toEqual({
      substitute_user_ids: [3],
      vacation_end_date: '2026-11-01',
      absence_status: 'vacation',
    });
    await call('set_vacation', { userId: 9, active: false });
    expect(fake.lastRequest('/accounts/users/9/deactivate-vacation')).toBeDefined();
    expect((await call('set_vacation', { active: true })).error).toMatchObject({ code: 'invalid_arguments' });
  });

  it('requires one source and one target to reassign', async () => {
    expect((await call('reassign_user', { fromUserId: 1, fromGroupId: 2, toUserId: 3 })).error).toMatchObject({
      code: 'invalid_arguments',
    });
    await call('reassign_user', { fromUserId: 1, toGroupId: 3 });
    expect(body('/accounts/users/reassign')).toEqual({ old_user: 1, new_group: 3 });
  });

  it('creates non-admin users by default and changes admin rights in the same update', async () => {
    await call('create_user', { email: 'bob@example.com' });
    expect(body('/accounts/users', 'POST')).toEqual({ email: 'bob@example.com', is_admin: false });

    await call('update_user', { userId: 5, isAdmin: true, firstName: 'Rob' });
    expect(body('/accounts/users/5', 'PATCH')).toEqual({ first_name: 'Rob', is_admin: true });
    expect(fake.lastRequest('/accounts/users/5/toggle-admin')).toBeUndefined();
  });

  it('creates groups and edits their members incrementally', async () => {
    fake.respond((request) =>
      request.path === '/accounts/groups' && request.method === 'GET'
        ? { body: [{ id: 11, name: 'QA', users: [1], type: 'regular' }] }
        : undefined,
    );
    expect((await call('create_group', { name: 'QA', userIds: [1] })).data).toEqual({
      id: 11,
      name: 'QA',
      type: 'regular',
      users: [1],
    });
    fake.respond((request) =>
      request.path === '/accounts/groups/11' && request.method === 'GET'
        ? { body: { id: 11, name: 'QA', photo: '', users: [1, 2] } }
        : undefined,
    );
    await call('update_group', { groupId: 11, addUserIds: [3], removeUserIds: [1] });
    expect(body('/accounts/groups/11', 'PUT')).toEqual({ name: 'QA', photo: '', users: [2, 3] });
  });

  it('lists notifications with the waiting task count', async () => {
    fake.respond((request) => {
      if (request.path === '/accounts/notifications') {
        return {
          body: {
            count: 1,
            results: [
              { id: 1, type: 'mention', status: 'new', text: 'Hi', task: { id: 2, name: 'Review' }, workflow: null },
            ],
          },
        };
      }
      return request.path === '/accounts/user/counters' ? { body: { tasks_count: 4 } } : undefined;
    });
    const { data } = await call('list_notifications', { status: 'new' });
    expect(data).toMatchObject({
      activeTaskCount: 4,
      items: [{ id: 1, type: 'mention', task: { id: 2, name: 'Review' }, workflow: null }],
    });
  });
});

describe('comments and task events', () => {
  it('edits, deletes and reacts to comments', async () => {
    await call('edit_comment', { commentId: 8, text: 'Fixed' });
    expect(body('/workflows/comments/8', 'PATCH')).toEqual({ text: 'Fixed' });
    await call('react_to_comment', { commentId: 8, reaction: '👍', remove: true });
    expect(body('/workflows/comments/8/delete-reaction')).toEqual({ value: '👍' });
    expect((await call('delete_comment', { commentId: 8 })).data).toEqual({ success: true });
  });

  it('lists task events', async () => {
    await call('list_task_events', { taskId: 3, includeComments: false });
    expect(fake.lastRequest('/v2/tasks/3/events')?.query).toEqual({ include_comments: 'false', limit: '20' });
  });
});

describe('datasets', () => {
  it('renames, removes and adds items by value', async () => {
    fake.respond((request) =>
      request.path === '/datasets/6' && request.method === 'GET'
        ? {
            body: {
              id: 6,
              name: 'Teams',
              items: [
                { id: 60, value: 'Sales' },
                { id: 61, value: 'Ops' },
              ],
            },
          }
        : undefined,
    );
    await call('update_dataset', {
      datasetId: 6,
      renameItems: [{ from: 'Sales', to: 'Revenue' }],
      removeItems: ['Ops'],
      addItems: ['Legal'],
    });
    expect(body('/datasets/items/60', 'PATCH')).toEqual({ value: 'Revenue' });
    expect(fake.lastRequest('/datasets/items/61')?.method).toBe('DELETE');
    expect(body('/datasets/6/items', 'POST')).toEqual([{ value: 'Legal', order: 1 }]);
    expect((await call('update_dataset', { datasetId: 6, removeItems: ['Missing'] })).error).toMatchObject({
      code: 'invalid_arguments',
    });

    fake.requests.length = 0;
    const duplicate = await call('update_dataset', { datasetId: 6, name: 'Units', addItems: ['Ops'] });
    expect(duplicate.error).toMatchObject({ code: 'invalid_arguments', detail: expect.stringContaining('"Ops"') });
    expect(fake.requests.map((request) => request.method)).toEqual(['GET']);
  });

  it('creates datasets with ordered items', async () => {
    await call('create_dataset', { name: 'Regions', items: ['EU', 'US'] });
    expect(body('/datasets', 'POST')).toEqual({
      name: 'Regions',
      description: '',
      items: [
        { value: 'EU', order: 0 },
        { value: 'US', order: 1 },
      ],
    });
  });
});
