import type { Client } from '@modelcontextprotocol/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { createFakePneumatic } from './fakePneumatic.js';
import { callTool, connectServer, lastBody } from './harness.js';

const APP_URL = 'https://app.pneumatic.test';

let fake: ReturnType<typeof createFakePneumatic>;
let client: Client;
let instances = 0;

const call = (name: string, args?: Record<string, unknown>) => callTool(client, name, args);
const body = (path: string, method: string) => lastBody(fake, path, method);

beforeEach(async () => {
  // A distinct API URL per test keeps the per-account people cache from leaking between tests.
  fake = createFakePneumatic(`https://pneumatic-${(instances += 1)}.test`);
  client = await connectServer(fake, { appUrl: APP_URL });
});

afterEach(async () => {
  await client.close();
});

const taskForm = {
  id: 5,
  name: 'Approve offer',
  due_date_tsp: 1_800_000_000,
  workflow: { id: 9, name: 'Offer #9', status: 0 },
  performers: [
    { type: 'user', source_id: 7, is_completed: false },
    { type: 'group', source_id: 3, is_completed: false },
  ],
  output: [
    { api_name: 'start', name: 'Start date', type: 'date', is_required: true, value: '' },
    { api_name: 'level', name: 'Level', type: 'dropdown', selections: ['Junior', 'Senior'], value: '' },
    { api_name: 'note', name: 'Note', type: 'string', value: 'kept' },
    { api_name: 'docs', name: 'Documents', type: 'file', value: '' },
  ],
  fieldsets: [],
};

describe('links, dates and names', () => {
  it('adds web links, ISO dates and performer names', async () => {
    fake.respond((request) => {
      if (request.path === '/v2/tasks/5') {
        return { body: taskForm };
      }
      if (request.path === '/accounts/users') {
        return { body: [{ id: 7, first_name: 'Ada', last_name: 'Lovelace', email: 'ada@example.com' }] };
      }
      return request.path === '/accounts/groups' ? { body: [{ id: 3, name: 'Legal' }] } : undefined;
    });
    const { data } = await call('get_task', { taskId: 5 });
    expect(data).toMatchObject({
      webUrl: `${APP_URL}/tasks/5/`,
      dueDate: '2027-01-15T08:00:00.000Z',
      workflow: { id: 9, webUrl: `${APP_URL}/workflows/9/` },
      performers: [
        { type: 'user', sourceId: 7, name: 'Ada Lovelace' },
        { type: 'group', sourceId: 3, name: 'Legal' },
      ],
    });
    expect(data).not.toHaveProperty('dueDateTsp');
  });

  it('names the starter of a workflow started with run_workflow', async () => {
    fake.respond((request) => {
      if (request.path === '/templates' && request.method === 'GET') {
        return { body: { count: 1, results: [{ id: 2, name: 'Hiring', kickoff: { fields: [], fieldsets: [] } }] } };
      }
      if (request.path === '/templates/2/run') {
        return { body: { id: 12, name: 'Hiring #12', status: 0, workflow_starter: 7, tasks: [] } };
      }
      return request.path === '/accounts/users'
        ? { body: [{ id: 7, first_name: 'Ada', last_name: 'Lovelace', email: 'ada@example.com' }] }
        : undefined;
    });
    const { data } = await call('run_workflow', { templateId: 2 });
    expect(data).toMatchObject({ id: 12, workflowStarterName: 'Ada Lovelace', webUrl: `${APP_URL}/workflows/12/` });
  });

  it('keeps working without names when the directory cannot be loaded', async () => {
    fake.respond((request) => {
      if (request.path === '/v2/tasks/5') {
        return { body: taskForm };
      }
      return request.path === '/accounts/users' ? { status: 403, body: { detail: 'Forbidden' } } : undefined;
    });
    const result = await call('get_task', { taskId: 5 });
    expect(result.isError).toBe(false);
    expect(result.data.performers[0]).not.toHaveProperty('name');
  });
});

describe('field checks before writes', () => {
  beforeEach(() => {
    fake.respond((request) =>
      request.path === '/v2/tasks/5' && request.method === 'GET' ? { body: taskForm } : undefined,
    );
  });

  it('converts ISO dates, keeps valid options and sends only supplied fields', async () => {
    const result = await call('complete_task', {
      taskId: 5,
      output: {
        start: '2027-01-15T08:00:00Z',
        level: 'Senior',
        docs: '[cv.pdf](https://app.pneumatic.test/files/abc12345)',
      },
    });
    expect(result.isError).toBe(false);
    expect(body('/v2/tasks/5/complete', 'POST')).toEqual({
      output: { start: 1_800_000_000, level: 'Senior', docs: ['[cv.pdf](https://app.pneumatic.test/files/abc12345)'] },
    });
  });

  it('explains wrong keys, options and missing required fields without calling complete', async () => {
    const label = await call('complete_task', { taskId: 5, output: { 'Start date': 1_800_000_000 } });
    expect(label.error.detail).toContain('use api_name "start"');
    const option = await call('complete_task', { taskId: 5, output: { start: 1, level: 'Lead' } });
    expect(option.error.detail).toContain('["Junior","Senior"]');
    const missing = await call('complete_task', { taskId: 5, output: { level: 'Junior' } });
    expect(missing.error.detail).toContain('Required fields are empty: start');
    const file = await call('complete_task', { taskId: 5, output: { start: 1, docs: ['abc12345'] } });
    expect(file.error.detail).toContain('"[name](url)"');
    const long = await call('complete_task', { taskId: 5, output: { start: 1, note: 'x'.repeat(141) } });
    expect(long.error.detail).toContain('at most 140');
    expect(fake.requests.filter((request) => request.path === '/v2/tasks/5/complete')).toHaveLength(0);
  });

  it('does not require hidden fields, skips dataset options and counts characters, not UTF-16 units', async () => {
    fake.respond((request) =>
      request.path === '/v2/tasks/6' && request.method === 'GET'
        ? {
            body: {
              id: 6,
              output: [
                { api_name: 'sync', name: 'Sync', type: 'string', is_required: true, is_hidden: true, value: '' },
                { api_name: 'team', name: 'Team', type: 'dropdown', dataset: 3, selections: [{ value: 'Ops' }] },
                { api_name: 'title', name: 'Title', type: 'string' },
              ],
              fieldsets: [],
            },
          }
        : undefined,
    );
    const result = await call('complete_task', { taskId: 6, output: { team: 'Sales', title: '😀'.repeat(140) } });
    expect(result.isError).toBe(false);
  });

  it('converts kickoff dates on update_workflow without demanding unrelated fields', async () => {
    fake.respond((request) =>
      request.path === '/workflows/7' && request.method === 'GET'
        ? {
            body: {
              id: 7,
              kickoff: {
                output: [
                  { api_name: 'start', name: 'Start', type: 'date', value: '' },
                  { api_name: 'owner', name: 'Owner', type: 'user', is_required: true, value: '' },
                ],
                fieldsets: [],
              },
            },
          }
        : undefined,
    );
    await call('update_workflow', { workflowId: 7, kickoff: { start: '2027-01-15T08:00:00Z' } });
    expect(body('/workflows/7', 'PATCH')).toMatchObject({ kickoff: { start: 1_800_000_000 } });
  });

  it('requires every required kickoff field when starting a workflow', async () => {
    fake.respond((request) =>
      request.path === '/templates' && request.method === 'GET'
        ? {
            body: {
              count: 1,
              results: [
                {
                  id: 2,
                  name: 'Hiring',
                  kickoff: {
                    fields: [{ api_name: 'candidate', name: 'Candidate', type: 'string', is_required: true }],
                    fieldsets: [],
                  },
                },
              ],
            },
          }
        : undefined,
    );
    const missing = await call('run_workflow', { templateId: 2 });
    expect(missing.error.detail).toContain('candidate (Candidate)');
    await call('run_workflow', { templateId: 2, kickoff: { candidate: 'Ada' } });
    expect(body('/templates/2/run', 'POST')).toMatchObject({ kickoff: { candidate: 'Ada' } });
  });
});
