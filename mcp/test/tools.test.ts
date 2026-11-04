import type { Client } from '@modelcontextprotocol/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { RemoteFetcher } from '../src/core/ports.js';
import { MAX_RESULT_BYTES } from '../src/presenters/index.js';
import { ConnectorError } from '../src/core/errors.js';
import { toTimestamp } from '../src/tools/shared.js';
import { createFakePneumatic, VALID_API_KEY } from './fakePneumatic.js';
import { callTool, connectServer, type ConnectOptions } from './harness.js';

let fake: ReturnType<typeof createFakePneumatic>;
let client: Client;
let fetchRemote: ReturnType<typeof vi.fn<RemoteFetcher>>;

const connect = (options?: ConnectOptions) => connectServer(fake, { fetchRemote, ...options });
const call = (name: string, args?: Record<string, unknown>, mcpClient = client) => callTool(mcpClient, name, args);

beforeEach(async () => {
  fake = createFakePneumatic();
  fetchRemote = vi.fn<RemoteFetcher>();
  client = await connect();
});

afterEach(async () => {
  await client.close();
});

describe('tool catalog', () => {
  it('exposes every tool with a title, safety annotations and a strict input schema', async () => {
    const { tools } = await client.listTools();
    expect(tools.map((tool) => tool.name).sort()).toEqual([
      'add_task_performer',
      'add_template_step',
      'clone_template',
      'comment_on_task',
      'comment_on_workflow',
      'complete_task',
      'count_workflows',
      'create_dataset',
      'create_group',
      'create_template',
      'create_template_from_library',
      'create_user',
      'deactivate_user',
      'delete_comment',
      'delete_dataset',
      'delete_group',
      'delete_template',
      'download_file',
      'edit_comment',
      'finish_workflow',
      'generate_template_steps',
      'get_assignment_count',
      'get_current_user',
      'get_dashboard',
      'get_dataset',
      'get_task',
      'get_template',
      'get_template_kickoff',
      'get_template_step_stats',
      'get_workflow',
      'get_workflow_field_values',
      'list_attachments',
      'list_datasets',
      'list_groups',
      'list_highlights',
      'list_library_templates',
      'list_notifications',
      'list_task_events',
      'list_tasks',
      'list_templates',
      'list_users',
      'list_workflow_events',
      'list_workflows',
      'mark_notifications_read',
      'react_to_comment',
      'reassign_user',
      'remove_task_performer',
      'remove_template_fields',
      'remove_template_step',
      'resume_workflow',
      'return_workflow_to_task',
      'revert_task',
      'run_workflow',
      'set_checklist_item',
      'set_task_due_date',
      'set_vacation',
      'snooze_workflow',
      'terminate_workflow',
      'update_dataset',
      'update_group',
      'update_template',
      'update_template_kickoff',
      'update_template_step',
      'update_user',
      'update_workflow',
      'upload_file',
    ]);
    for (const tool of tools) {
      expect(tool.title, tool.name).toBeTruthy();
      expect(tool.annotations?.readOnlyHint, tool.name).toBeTypeOf('boolean');
      expect(tool.inputSchema.additionalProperties, tool.name).toBe(false);
      if (!tool.annotations?.readOnlyHint) {
        expect(tool.annotations?.destructiveHint, tool.name).toBeTypeOf('boolean');
      }
    }
  });

  it('asks for confirmation of every destructive tool in the server instructions', async () => {
    const { tools } = await client.listTools();
    const instructions = client.getInstructions() ?? '';
    for (const tool of tools.filter((item) => item.annotations?.destructiveHint)) {
      expect(instructions, tool.name).toContain(tool.name);
    }
  });

  it('marks irreversible tools as destructive', async () => {
    const { tools } = await client.listTools();
    const destructive = tools.filter((tool) => tool.annotations?.destructiveHint).map((tool) => tool.name);
    expect(destructive).toEqual(
      expect.arrayContaining([
        'terminate_workflow',
        'finish_workflow',
        'revert_task',
        'return_workflow_to_task',
        'delete_template',
        'reassign_user',
        'deactivate_user',
        'delete_group',
        'delete_comment',
        'delete_dataset',
        'remove_template_step',
        'remove_template_fields',
      ]),
    );
  });
});

describe('tool calls', () => {
  it('runs a workflow with kickoff values and an ISO due date', async () => {
    await call('run_workflow', {
      templateId: 12,
      name: 'Onboard Ada',
      kickoff: { 'field-1': 'Ada', 'field-2': ['a', 'b'] },
      dueDate: '2026-10-15T09:00:00Z',
    });
    const request = fake.lastRequest('/templates/12/run');
    expect(request?.method).toBe('POST');
    expect(request?.body).toEqual({
      name: 'Onboard Ada',
      kickoff: { 'field-1': 'Ada', 'field-2': ['a', 'b'] },
      due_date_tsp: Date.parse('2026-10-15T09:00:00Z') / 1000,
    });
  });

  it('maps workflow filters to comma-separated query params', async () => {
    await call('list_workflows', { status: 'running', templateIds: [1, 2], currentPerformerIds: [5] });
    expect(fake.lastRequest('/workflows')?.query).toEqual({
      status: 'running',
      template_id: '1,2',
      current_performer: '5',
      limit: '20',
    });
  });

  it('lists active tasks by default', async () => {
    await call('list_tasks');
    expect(fake.lastRequest('/v3/tasks')?.query).toEqual({ is_completed: 'false', limit: '20' });
  });

  it('completes a task with output values', async () => {
    fake.respond((request) =>
      request.path === '/v2/tasks/3' && request.method === 'GET'
        ? { body: { id: 3, output: [{ api_name: 'field-9', name: 'Amount', type: 'number' }], fieldsets: [] } }
        : undefined,
    );
    await call('complete_task', { taskId: 3, output: { 'field-9': 42 } });
    expect(fake.lastRequest('/v2/tasks/3/complete')?.body).toEqual({ output: { 'field-9': 42 } });
  });

  it('clears a due date with DELETE and sets it with POST', async () => {
    await call('set_task_due_date', { taskId: 4, dueDate: null });
    expect(fake.lastRequest('/v2/tasks/4/due-date')?.method).toBe('DELETE');

    await call('set_task_due_date', { taskId: 4, dueDate: 1_800_000_000 });
    expect(fake.lastRequest('/v2/tasks/4/due-date')?.body).toEqual({ due_date_tsp: 1_800_000_000 });
  });

  it('routes performer changes by performer kind', async () => {
    await call('add_task_performer', { taskId: 5, groupId: 8 });
    expect(fake.lastRequest('/v2/tasks/5/create-group-performer')?.body).toEqual({ group_id: 8 });

    await call('remove_task_performer', { taskId: 5, guestEmail: 'guest@example.com' });
    expect(fake.lastRequest('/v2/tasks/5/delete-guest-performer')?.body).toEqual({ email: 'guest@example.com' });

    const ambiguous = await call('add_task_performer', { taskId: 5, userId: 1, groupId: 2 });
    expect(ambiguous.isError).toBe(true);
    expect(ambiguous.error).toMatchObject({
      code: 'invalid_arguments',
      detail: expect.stringContaining('exactly one'),
    });
  });

  it('switches checklist endpoint by checked flag', async () => {
    await call('set_checklist_item', { checklistId: 9, selectionId: 99, checked: false });
    expect(fake.lastRequest('/v2/tasks/checklists/9/unmark')?.body).toEqual({ selection_id: 99 });
  });

  it('queries the dashboard for a period and leaves the period end to the API', async () => {
    await call('get_dashboard', { scope: 'tasks', breakdown: 'template', dateFrom: 1_700_000_000 });
    expect(fake.lastRequest('/reports/dashboard/tasks/breakdown')?.query).toEqual({ date_from_tsp: '1700000000' });
  });

  it('requests the current dashboard snapshot without dates', async () => {
    await call('get_dashboard', { scope: 'workflows', dateFrom: 1_700_000_000, currentOnly: true });
    expect(fake.lastRequest('/reports/dashboard/workflows/overview')?.query).toEqual({ now: 'true' });
  });

  it('reports empty successful responses', async () => {
    const result = await call('terminate_workflow', { workflowId: 1 });
    expect(result).toMatchObject({ isError: false, data: { success: true }, truncated: false });
    expect(JSON.parse(result.text)).toEqual({ data: { success: true }, truncated: false });
  });

  it('rejects unknown arguments instead of ignoring them', async () => {
    const result = await call('get_task', { taskId: 1, task_id: 1 });
    expect(result.isError).toBe(true);
    expect(fake.lastRequest('/v2/tasks/1')).toBeUndefined();
  });

  it('rejects invalid dates before calling the API', async () => {
    const result = await call('snooze_workflow', { workflowId: 2, until: 'next tuesday' });
    expect(result.isError).toBe(true);
    expect(result.error).toMatchObject({
      code: 'invalid_arguments',
      detail: expect.stringContaining('Invalid date-time'),
    });
    expect(fake.lastRequest('/workflows/2/snooze')).toBeUndefined();
  });
});

describe('errors', () => {
  it('surfaces Pneumatic validation messages with a stable code', async () => {
    fake.respond((request) =>
      request.path === '/workflows/2/snooze'
        ? { status: 400, body: { code: 'validation_error', message: 'Date must be in the future' } }
        : undefined,
    );
    const result = await call('snooze_workflow', { workflowId: 2, until: '2020-01-01T00:00:00Z' });
    expect(result.isError).toBe(true);
    expect(result.error).toEqual({
      code: 'validation_error',
      message: expect.any(String),
      retryable: false,
      status: 400,
      detail: 'Date must be in the future',
    });
  });

  it('marks failed reads as retryable and failed writes as uncertain', async () => {
    const timeout: typeof fetch = async () => {
      throw new DOMException('The operation timed out.', 'TimeoutError');
    };
    const isolated = await connect({ fetchFn: timeout });
    const read = await call('get_task', { taskId: 1 }, isolated);
    expect(read.error).toMatchObject({ code: 'timeout', retryable: true });
    const write = await call('complete_task', { taskId: 1 }, isolated);
    expect(write.error).toMatchObject({ code: 'timeout', retryable: false });
    expect(write.error.message).toContain('check the current state before retrying');
    await isolated.close();
  });

  it('lets the model retry writes rejected by rate limits', async () => {
    fake.respond((request) =>
      request.path === '/v2/tasks/1/comment' ? { status: 429, body: { detail: 'Throttled' } } : undefined,
    );
    expect((await call('comment_on_task', { taskId: 1, text: 'Hi' })).error).toMatchObject({
      code: 'rate_limited',
      retryable: true,
    });
  });

  it('maps missing objects to not_found', async () => {
    fake.respond((request) =>
      request.path === '/v2/tasks/404' ? { status: 404, body: { detail: 'Not found.' } } : undefined,
    );
    expect((await call('get_task', { taskId: 404 })).error).toMatchObject({ code: 'not_found', status: 404 });
  });
});

describe('compact results', () => {
  it('returns task details with camelCase keys, named statuses and file links', async () => {
    fake.respond((request) =>
      request.path === '/v2/tasks/3'
        ? {
            body: {
              id: 3,
              name: 'Review contract',
              api_name: 'task-1',
              status: 'active',
              description: 'Check the draft',
              contains_comments: true,
              workflow: { id: 10, status: 3, name: 'Contract #10', template_name: 'Contracts' },
              performers: [{ type: 'user', source_id: 7, is_completed: false, date_completed_tsp: null }],
              output: [
                {
                  id: 1,
                  api_name: 'field-file',
                  name: 'Signed copy',
                  type: 'file',
                  is_required: true,
                  value: 'https://app.pneumatic.test/files/a, https://app.pneumatic.test/files/b',
                  markdown_value:
                    '[a, b.pdf](https://app.pneumatic.test/files/a), [c.pdf](https://app.pneumatic.test/files/b)',
                  selections: [],
                },
                {
                  id: 2,
                  api_name: 'field-choice',
                  name: 'Decision',
                  type: 'radio',
                  value: '',
                  selections: ['Yes', 'No'],
                },
              ],
              fieldsets: [],
              checklists: [
                { id: 5, api_name: 'cl-1', selections: [{ id: 50, api_name: 's', value: 'Read', is_selected: true }] },
              ],
              revert_tasks: [],
              sub_workflows: [],
            },
          }
        : undefined,
    );
    const { data } = await call('get_task', { taskId: 3 });
    expect(data).toMatchObject({
      id: 3,
      apiName: 'task-1',
      status: 'active',
      workflow: { id: 10, status: 'snoozed', templateName: 'Contracts' },
      performers: [{ type: 'user', sourceId: 7, isCompleted: false }],
      checklists: [{ id: 5, apiName: 'cl-1', selections: [{ id: 50, value: 'Read', isSelected: true }] }],
    });
    expect(data.output[0].fileLinks).toEqual([
      '[a, b.pdf](https://app.pneumatic.test/files/a)',
      '[c.pdf](https://app.pneumatic.test/files/b)',
    ]);
    expect(data.output[1]).toMatchObject({ apiName: 'field-choice', selections: ['Yes', 'No'] });
    expect(data).not.toHaveProperty('containsComments');
  });

  it('pages lists and names event types', async () => {
    fake.respond((request) =>
      request.path === '/workflows/4/events'
        ? {
            body: {
              count: 3,
              results: [
                { id: 1, type: 5, text: 'Looks good', created_tsp: 1.5, task: { id: 2, name: 'Review', number: 1 } },
                { id: 2, type: 3, text: null, created_tsp: 1.2, task: null, status: 'deleted' },
              ],
            },
          }
        : undefined,
    );
    const { data } = await call('list_workflow_events', { workflowId: 4, limit: 2 });
    expect(data.items[0]).toMatchObject({ id: 1, type: 'comment', text: 'Looks good', task: { id: 2, number: 1 } });
    expect(data.items[1]).toMatchObject({ type: 'task_complete', deleted: true });
    expect(data.page).toEqual({ limit: 2, offset: 0, returned: 2, total: 3, nextOffset: 2 });
  });

  it('bounds large results and flags truncation', async () => {
    const results = Array.from({ length: 100 }, (_, index) => ({
      id: index + 1,
      name: `Template ${index}`,
      description: 'x'.repeat(1500),
      is_active: true,
    }));
    fake.respond((request) => (request.path === '/templates' ? { body: { count: 500, results } } : undefined));
    const result = await call('list_templates', { limit: 100 });
    expect(result.truncated).toBe(true);
    expect(Buffer.byteLength(result.text)).toBeLessThanOrEqual(MAX_RESULT_BYTES);
    expect(result.data.page.nextOffset).toBe(result.data.items.length);
    for (const item of result.data.items) {
      expect(item.name).toMatch(/^Template \d+$/);
    }
  });

  it('never blanks identifiers or file links when prose exceeds the text budget', async () => {
    const output = Array.from({ length: 20 }, (_, index) => ({
      api_name: `field-${index}`,
      name: `File ${index}`,
      type: 'file',
      description: 'd'.repeat(1500),
      value: '',
      markdown_value: `[f${index}.pdf](https://app.pneumatic.test/files/file-${index}-abcd)`,
    }));
    fake.respond((request) =>
      request.path === '/v2/tasks/8'
        ? { body: { id: 8, name: 'Big', description: 'x'.repeat(8000), output } }
        : undefined,
    );
    const { data, truncated } = await call('get_task', { taskId: 8 });
    expect(truncated).toBe(true);
    expect(data.output).toHaveLength(20);
    data.output.forEach((field: { apiName: string; type: string; fileLinks: string[] }, index: number) => {
      expect(field).toMatchObject({ apiName: `field-${index}`, type: 'file' });
      expect(field.fileLinks).toEqual([`[f${index}.pdf](https://app.pneumatic.test/files/file-${index}-abcd)`]);
    });
  });

  it('cuts the nested list that owns the bulk before whole items', async () => {
    const tasks = Array.from({ length: 10 }, (_, index) => ({
      api_name: `task-${index}`,
      name: `Step ${index}`,
      number: index + 1,
      fields: [
        {
          api_name: `field-${index}`,
          name: 'Choice',
          type: 'dropdown',
          selections: Array.from({ length: 200 }, (_, option) => ({ value: `Option ${option} ${'o'.repeat(40)}` })),
        },
      ],
    }));
    fake.respond((request) =>
      request.path === '/templates/5' ? { body: { id: 5, name: 'Huge', kickoff: {}, tasks } } : undefined,
    );
    const { data, truncated, text } = await call('get_template', { templateId: 5 });
    expect(truncated).toBe(true);
    expect(Buffer.byteLength(text)).toBeLessThanOrEqual(MAX_RESULT_BYTES);
    expect(data.tasks).toHaveLength(10);
    expect(data.tasks[0].fields[0].selections.length).toBeLessThan(200);
  });

  it('keeps page items and their pagination when only nested lists are cut', async () => {
    const huge = {
      id: 1,
      name: 'Huge',
      tasks: Array.from({ length: 100 }, (_, id) => ({ id, name: 'n'.repeat(1500) })),
    };
    fake.respond((request) =>
      request.path === '/workflows' ? { body: { count: 2, results: [huge, { id: 2, name: 'Small' }] } } : undefined,
    );
    const { data, truncated } = await call('list_workflows', { limit: 2 });
    expect(truncated).toBe(true);
    expect(data.items.map((item: { id: number }) => item.id)).toEqual([1, 2]);
    expect(data.items[0].tasks.length).toBeLessThan(100);
    expect(data.page).toMatchObject({ returned: 2, nextOffset: null });
  });

  it('bounds multi-megabyte responses quickly', async () => {
    const results = Array.from({ length: 100 }, (_, id) => ({
      id,
      name: `W${id}`,
      tasks: Array.from({ length: 100 }, (_, task) => ({
        id: task,
        name: 'n'.repeat(300),
        performers: Array.from({ length: 20 }, (_, user) => ({ type: 'user', source_id: user })),
      })),
    }));
    fake.respond((request) => (request.path === '/workflows' ? { body: { count: 100, results } } : undefined));
    const started = performance.now();
    const { data, text } = await call('list_workflows', { limit: 100 });
    expect(performance.now() - started).toBeLessThan(2000);
    expect(Buffer.byteLength(text)).toBeLessThanOrEqual(MAX_RESULT_BYTES);
    expect(data.items.length).toBeGreaterThan(0);
    expect(data.page).toMatchObject({ returned: data.items.length, nextOffset: data.items.length });
  });

  it('keeps long ID lists up to 1000 entries', async () => {
    fake.respond((request) =>
      request.path === '/accounts/user'
        ? { body: { id: 7, subordinates_ids: Array.from({ length: 1500 }, (_, index) => index) } }
        : undefined,
    );
    const { data, truncated } = await call('get_current_user');
    expect(data.subordinatesIds).toHaveLength(1000);
    expect(truncated).toBe(true);
  });

  it('pages the dashboard breakdown locally because the API returns every row', async () => {
    const rows = Array.from({ length: 30 }, (_, index) => ({
      template_id: index + 1,
      template_name: `T${index + 1}`,
      started: 1,
    }));
    fake.respond((request) => (request.path === '/reports/dashboard/workflows/breakdown' ? { body: rows } : undefined));
    const { data } = await call('get_dashboard', { scope: 'workflows', breakdown: 'template', limit: 20, offset: 20 });
    expect(data.items.map((item: { templateId: number }) => item.templateId)).toEqual(
      Array.from({ length: 10 }, (_, index) => index + 21),
    );
    expect(data.page).toMatchObject({ total: 30, nextOffset: null });
  });

  it('pages groups locally because the API returns them all', async () => {
    fake.respond((request) =>
      request.path === '/accounts/groups'
        ? { body: [1, 2, 3].map((id) => ({ id, name: `Group ${id}`, users: [id], type: 'regular', photo: null })) }
        : undefined,
    );
    const { data } = await call('list_groups', { limit: 2, offset: 1 });
    expect(data.items).toEqual([
      { id: 2, name: 'Group 2', type: 'regular', users: [2] },
      { id: 3, name: 'Group 3', type: 'regular', users: [3] },
    ]);
    expect(data.page).toMatchObject({ total: 3, nextOffset: null });
  });
});

describe('get_template_kickoff', () => {
  const template = (id: number) => ({
    id,
    name: `Template ${id}`,
    is_active: true,
    description: '',
    kickoff: {
      fields: [{ api_name: 'field-a', name: 'Client', type: 'dropdown', is_required: true, selections: ['A', 'B'] }],
      fieldsets: [
        {
          api_name: 'fs-1',
          name: 'Budget',
          rules: [],
          fields: [{ api_name: 'field-b', name: 'Amount', type: 'number', selections: undefined }],
        },
      ],
    },
  });

  it('finds the template in the access-filtered list across pages', async () => {
    fake.respond((request) => {
      if (request.path !== '/templates') {
        return undefined;
      }
      const offset = Number(request.query.offset ?? 0);
      const ids = offset === 0 ? Array.from({ length: 100 }, (_, index) => index + 1) : [150];
      return { body: { count: 101, results: ids.map(template) } };
    });
    const { data, isError } = await call('get_template_kickoff', { templateId: 150 });
    expect(isError).toBe(false);
    expect(data).toMatchObject({
      templateId: 150,
      name: 'Template 150',
      isActive: true,
      fields: [{ apiName: 'field-a', isRequired: true, selections: ['A', 'B'] }],
      fieldsets: [{ apiName: 'fs-1', fields: [{ apiName: 'field-b', type: 'number' }] }],
    });
    expect(fake.requests.filter((request) => request.path === '/templates')).toHaveLength(2);
  });

  it('reports templates outside the user access as not found', async () => {
    fake.respond((request) =>
      request.path === '/templates' ? { body: { count: 1, results: [template(1)] } } : undefined,
    );
    expect((await call('get_template_kickoff', { templateId: 2 })).error).toMatchObject({ code: 'not_found' });
  });
});

describe('files', () => {
  it('uploads text content and returns a file field value', async () => {
    const { data, isError } = await call('upload_file', { filename: 'report.md', contentText: '# Weekly report' });
    expect(isError).toBe(false);
    expect(data).toEqual({
      fileId: 'file-1-0000',
      name: 'report.md',
      contentType: 'text/markdown',
      size: 15,
      url: `${fake.filesUrl}/file-1-0000`,
      fieldValue: `[report.md](${fake.filesUrl}/file-1-0000)`,
    });
    expect(fake.files.get('file-1-0000')?.data.toString()).toBe('# Weekly report');
    expect(fake.lastRequest('/files/upload')?.authorization).toBe(`Bearer ${VALID_API_KEY}`);
  });

  it('refreshes the storage token cache through the backend once', async () => {
    fake.state.storageCacheWarm = false;
    const { isError } = await call('upload_file', {
      filename: 'a.txt',
      contentBase64: Buffer.from('hi').toString('base64'),
    });
    expect(isError).toBe(false);
    expect(fake.requests.map((request) => request.path)).toEqual(['/files/upload', '/accounts/user', '/files/upload']);
  });

  it('imports a public URL through the guarded fetcher and keeps the source name', async () => {
    fetchRemote.mockResolvedValue({
      data: Buffer.from('%PDF-1.7'),
      contentType: 'application/pdf',
      filename: 'offer.pdf',
    });
    const { data } = await call('upload_file', { sourceUrl: 'https://example.com/download?id=1' });
    expect(fetchRemote).toHaveBeenCalledWith(new URL('https://example.com/download?id=1'), 25 * 1024 * 1024);
    expect(data).toMatchObject({ name: 'offer.pdf', contentType: 'application/pdf', size: 8 });
  });

  it('reports source download failures without claiming an uncertain write', async () => {
    fetchRemote.mockRejectedValue(new ConnectorError('source_error', 'The source URL returned HTTP 404'));
    const { error } = await call('upload_file', { sourceUrl: 'https://example.com/missing.pdf' });
    expect(error).toMatchObject({ code: 'source_error', detail: 'The source URL returned HTTP 404' });
    expect(error.message).not.toContain('outcome may be unknown');
    expect(fake.requests).toHaveLength(0);
  });

  it('fails cleanly when the storage still rejects the key after a refresh', async () => {
    fake.state.storageCacheWarm = false;
    fake.respond((request) => (request.path === '/accounts/user' ? { body: { id: 7 } } : undefined));
    const { error } = await call('upload_file', { filename: 'a.txt', contentText: 'a' });
    expect(error).toMatchObject({ code: 'unauthorized', status: 401 });
    expect(fake.requests.map((request) => request.path)).toEqual(['/files/upload', '/accounts/user', '/files/upload']);
  });

  it('returns only metadata for files above the inline limit', async () => {
    fake.files.set('large-file-01', { name: 'video.mp4', type: 'video/mp4', data: Buffer.alloc(4 * 1024 * 1024) });
    const { data, content } = await call('download_file', { fileId: 'large-file-01' });
    expect(data).toMatchObject({ name: 'video.mp4', size: 4 * 1024 * 1024, inline: false });
    expect(content).toHaveLength(1);
  });

  it('rejects private source URLs and ambiguous sources before any request', async () => {
    const privateUrl = await call('upload_file', { sourceUrl: 'https://169.254.169.254/latest' });
    expect(privateUrl.error).toMatchObject({ code: 'invalid_arguments' });
    const twoSources = await call('upload_file', {
      filename: 'a.txt',
      contentText: 'a',
      sourceUrl: 'https://example.com/a',
    });
    expect(twoSources.error).toMatchObject({ code: 'invalid_arguments' });
    const noName = await call('upload_file', { contentText: 'a' });
    expect(noName.error).toMatchObject({ code: 'invalid_arguments' });
    expect(fetchRemote).not.toHaveBeenCalled();
    expect(fake.requests).toHaveLength(0);
  });

  it('downloads text and image files as MCP content', async () => {
    fake.files.set('text-file-01', { name: 'notes.txt', type: 'text/plain', data: Buffer.from('hello') });
    fake.files.set('image-file-1', { name: 'photo.png', type: 'image/png', data: Buffer.from([137, 80, 78, 71]) });

    const text = await call('download_file', { url: `[notes.txt](${fake.filesUrl}/text-file-01)` });
    expect(text.data).toMatchObject({ fileId: 'text-file-01', name: 'notes.txt', size: 5, inline: true });
    expect(text.content[1]).toEqual({
      type: 'resource',
      resource: { uri: `${fake.filesUrl}/text-file-01`, mimeType: 'text/plain', text: 'hello' },
    });

    const image = await call('download_file', { fileId: 'image-file-1' });
    expect(image.content[1]).toEqual({
      type: 'image',
      data: Buffer.from([137, 80, 78, 71]).toString('base64'),
      mimeType: 'image/png',
    });
  });

  it('refuses to send the API key to foreign file URLs', async () => {
    const result = await call('download_file', { url: 'https://evil.example/files/abcdefgh' });
    expect(result.error).toMatchObject({ code: 'invalid_arguments' });
    expect(fake.requests).toHaveLength(0);
  });

  it('reports missing storage configuration', async () => {
    const isolated = await connect({ storage: false });
    expect((await call('download_file', { fileId: 'abcdefgh' }, isolated)).error).toMatchObject({
      code: 'not_configured',
    });
    await isolated.close();
  });

  it('lists attachments', async () => {
    fake.respond((request) =>
      request.path === '/attachments'
        ? {
            body: {
              count: 1,
              results: [
                { id: 1, file_id: 'abc', url: `${fake.filesUrl}/abc`, access_type: 'restricted', source_type: 'Task' },
              ],
            },
          }
        : undefined,
    );
    const { data } = await call('list_attachments');
    expect(data.items).toEqual([
      { id: 1, fileId: 'abc', url: `${fake.filesUrl}/abc`, accessType: 'restricted', sourceType: 'Task' },
    ]);
  });
});

describe('toTimestamp', () => {
  it('accepts seconds, milliseconds, numeric strings and ISO dates', () => {
    expect(toTimestamp(1_800_000_000)).toBe(1_800_000_000);
    expect(toTimestamp(1_800_000_000_000)).toBe(1_800_000_000);
    expect(toTimestamp('1800000000')).toBe(1_800_000_000);
    expect(toTimestamp('2027-01-15T08:00:00.000Z')).toBe(Date.parse('2027-01-15T08:00:00.000Z') / 1000);
    expect(toTimestamp('2027-01-15T11:00:00+03:00')).toBe(toTimestamp('2027-01-15T08:00:00Z'));
    expect(toTimestamp('2028-02-29T00:00:00Z')).toBe(Date.parse('2028-02-29T00:00:00Z') / 1000);
  });

  it('rejects ambiguous and non-finite dates', () => {
    for (const value of [
      'January 15',
      '2027-01-15',
      'next Tuesday',
      '2026-02-29T09:00:00Z',
      '2026-02-31T09:00:00Z',
      '2026-04-31T09:00:00+03:00',
      '2026-13-01T09:00:00Z',
      Infinity,
      NaN,
    ]) {
      expect(() => toTimestamp(value)).toThrow('Invalid date-time');
    }
  });
});
