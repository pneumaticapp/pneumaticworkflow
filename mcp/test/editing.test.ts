import type { Client } from '@modelcontextprotocol/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { createFakePneumatic } from './fakePneumatic.js';
import { callTool, connectServer, lastBody } from './harness.js';

let fake: ReturnType<typeof createFakePneumatic>;
let client: Client;

const connect = (capabilities?: Record<string, unknown>) => connectServer(fake, { capabilities });
const call = (name: string, args?: Record<string, unknown>, mcpClient = client) => callTool(mcpClient, name, args);
const sent = (path: string, method: string) => lastBody(fake, path, method);

const chained = (field: string | null) => [
  {
    action: 'start_task',
    order: 1,
    rules: [
      {
        predicates: [
          field
            ? { field_type: 'task', operator: 'completed', field, value: null }
            : { field_type: 'kickoff', operator: 'completed', field: null, value: null },
        ],
      },
    ],
  },
];

const template = () => ({
  id: 4,
  name: 'Hiring',
  is_active: true,
  owners: [{ type: 'user', source_id: '7', role: 'owner' }],
  kickoff: { fields: [{ api_name: 'candidate', name: 'Candidate', type: 'string', order: 1 }], fieldsets: [] },
  tasks: [
    {
      number: 1,
      api_name: 'task-screen',
      name: 'Screen',
      raw_performers: [{ type: 'user', source_id: '7' }],
      fields: [
        { api_name: 'field-a', name: 'A', type: 'string', order: 2 },
        { api_name: 'field-b', name: 'B', type: 'string', order: 1 },
      ],
      conditions: chained(null),
    },
    {
      number: 2,
      api_name: 'task-offer',
      name: 'Offer',
      raw_performers: [],
      fields: [],
      conditions: chained('task-screen'),
    },
  ],
});

beforeEach(async () => {
  fake = createFakePneumatic();
  fake.respond((request) => {
    if (request.path === '/accounts/user') {
      return { body: { id: 7 } };
    }
    return request.path === '/templates/4' && request.method === 'GET' ? { body: template() } : undefined;
  });
  client = await connect();
});

afterEach(async () => {
  await client.close();
});

describe('template editing', () => {
  it('inserts a step into the chain and rewires the following step', async () => {
    await call('add_template_step', { templateId: 4, position: 2, step: { name: 'Interview' } });
    const { tasks } = sent('/templates/4', 'PUT');
    expect(tasks.map((task: any) => [task.number, task.name])).toEqual([
      [1, 'Screen'],
      [2, 'Interview'],
      [3, 'Offer'],
    ]);
    const interview = tasks[1];
    expect(interview.conditions[0].rules[0].predicates[0].field).toBe('task-screen');
    expect(tasks[2].conditions[0].rules[0].predicates[0].field).toBe(interview.api_name);
    expect(interview.raw_performers).toEqual([{ type: 'user', source_id: 7 }]);
  });

  it('updates one step and appends fields below the existing ones', async () => {
    await call('update_template_step', {
      templateId: 4,
      stepApiName: 'task-screen',
      name: 'Phone screen',
      dueInHours: 24,
      addFields: [{ name: 'Score', type: 'number' }],
    });
    const [screen, offer] = sent('/templates/4', 'PUT').tasks;
    expect(screen).toMatchObject({
      name: 'Phone screen',
      raw_due_date: { duration: '1 00:00:00', source_id: 'task-screen' },
    });
    expect(screen.fields.map((item: any) => [item.api_name, item.name, item.order])).toEqual([
      ['field-a', 'A', 2],
      ['field-b', 'B', 1],
      [undefined, 'Score', 0],
    ]);
    expect(offer.name).toBe('Offer');
    expect((await call('update_template_step', { templateId: 4, stepApiName: 'nope', name: 'x' })).error).toMatchObject(
      {
        code: 'invalid_arguments',
      },
    );
  });

  it('removes a step and lets its successor wait for the predecessor instead', async () => {
    await call('remove_template_step', { templateId: 4, stepApiName: 'task-screen' });
    const { tasks } = sent('/templates/4', 'PUT');
    expect(tasks).toHaveLength(1);
    expect(tasks[0]).toMatchObject({ number: 1, api_name: 'task-offer' });
    expect(tasks[0].conditions[0].rules[0].predicates[0].field_type).toBe('kickoff');
  });

  it('rewires a chained step that also has a skip condition and keeps that condition', async () => {
    const skip = {
      action: 'skip_task',
      order: 2,
      rules: [{ predicates: [{ field_type: 'kickoff', operator: 'completed' }] }],
    };
    fake.respond((request) => {
      if (request.path !== '/templates/4' || request.method !== 'GET') {
        return undefined;
      }
      const current = template();
      (current.tasks[1] as any).conditions = [...chained('task-screen'), skip];
      return { body: current };
    });
    await call('add_template_step', { templateId: 4, position: 2, step: { name: 'Interview' } });
    const [, interview, offer] = sent('/templates/4', 'PUT').tasks;
    expect(offer.conditions).toHaveLength(2);
    expect(offer.conditions.find((item: any) => item.action === 'skip_task')).toEqual(skip);
    expect(offer.conditions.find((item: any) => item.action === 'start_task').rules[0].predicates[0].field).toBe(
      interview.api_name,
    );
  });

  it('gives every successor of a removed step a fresh start condition', async () => {
    fake.respond((request) => {
      if (request.path !== '/templates/4' || request.method !== 'GET') {
        return undefined;
      }
      const current = template();
      current.tasks.push({
        number: 3,
        api_name: 'task-docs',
        name: 'Docs',
        raw_performers: [],
        fields: [],
        conditions: chained('task-screen'),
      } as never);
      (current.tasks[0] as any).conditions = chained(null).map((condition) => ({
        ...condition,
        api_name: 'condition-x',
      }));
      return { body: current };
    });
    await call('remove_template_step', { templateId: 4, stepApiName: 'task-screen' });
    const tasks = sent('/templates/4', 'PUT').tasks;
    expect(tasks.map((task: any) => task.conditions[0].rules[0].predicates[0].field_type)).toEqual([
      'kickoff',
      'kickoff',
    ]);
    expect(JSON.stringify(tasks)).not.toContain('condition-x');
  });

  it('refuses removals that other parts of the template still refer to', async () => {
    fake.respond((request) => {
      if (request.path !== '/templates/4' || request.method !== 'GET') {
        return undefined;
      }
      const current = template();
      (current.tasks[1] as any).name = 'Offer for {{candidate}}';
      (current.tasks[1] as any).revert_task = 'task-screen';
      return { body: current };
    });
    const step = await call('remove_template_step', { templateId: 4, stepApiName: 'task-screen' });
    expect(step.error.detail).toContain('still refers to step task-screen');
    const kickoffField = await call('remove_template_fields', { templateId: 4, fieldApiNames: ['candidate'] });
    expect(kickoffField.error.detail).toContain('still refers to field candidate');
    expect(sent('/templates/4', 'PUT')).toBeUndefined();
  });

  it('refuses to remove a step whose fields other steps still use', async () => {
    fake.respond((request) => {
      if (request.path !== '/templates/4' || request.method !== 'GET') {
        return undefined;
      }
      const current = template();
      (current.tasks[1] as any).description = 'Use {{field-a}} from the screening';
      return { body: current };
    });
    const result = await call('remove_template_step', { templateId: 4, stepApiName: 'task-screen' });
    expect(result.error.detail).toContain('still refers to field field-a');
    expect(sent('/templates/4', 'PUT')).toBeUndefined();
  });

  it('reports a missing kickoff form when removing kickoff fields', async () => {
    fake.respond((request) =>
      request.path === '/templates/4' && request.method === 'GET'
        ? { body: { ...template(), kickoff: null } }
        : undefined,
    );
    const result = await call('remove_template_fields', { templateId: 4, fieldApiNames: ['candidate'] });
    expect(result.error).toMatchObject({ code: 'invalid_arguments', detail: 'The template has no kickoff form' });
    expect(sent('/templates/4', 'PUT')).toBeUndefined();
  });

  it('removes fields from a step on request', async () => {
    await call('remove_template_fields', { templateId: 4, stepApiName: 'task-screen', fieldApiNames: ['field-b'] });
    expect(sent('/templates/4', 'PUT').tasks[0].fields.map((item: any) => item.api_name)).toEqual(['field-a']);
  });

  it('edits kickoff fields and publishes the form', async () => {
    await call('update_template_kickoff', { templateId: 4, addFields: [{ name: 'Start', type: 'date' }] });
    expect(sent('/templates/4', 'PUT').kickoff.fields.map((item: any) => item.name)).toEqual(['Candidate', 'Start']);
    await call('update_template', { templateId: 4, isPublic: true });
    expect(sent('/templates/4', 'PUT')).toMatchObject({ is_public: true, name: 'Hiring' });
  });
});

describe('workflow filters and workload', () => {
  it('passes field and step filters to the workflow list', async () => {
    await call('list_workflows', { templateIds: [4], templateTaskApiName: 'task-offer', fieldApiNames: ['candidate'] });
    expect(fake.lastRequest('/workflows')?.query).toMatchObject({
      template_id: '4',
      template_task_api_name: 'task-offer',
      fields: 'candidate',
    });
  });

  it('counts assignments of a user or a group', async () => {
    fake.respond((request) => (request.path.endsWith('/count-workflows') ? { body: { count: 3 } } : undefined));
    expect((await call('get_assignment_count', { groupId: 2 })).data).toEqual({ count: 3 });
    expect(fake.lastRequest('/accounts/groups/2/count-workflows')).toBeDefined();
  });
});

describe('prompts', () => {
  it('lists scenarios and fills in their arguments', async () => {
    const { prompts } = await client.listPrompts();
    expect(prompts.map((prompt) => prompt.name)).toEqual(
      expect.arrayContaining(['triage_inbox', 'weekly_report', 'start_process', 'offboard_user', 'design_process']),
    );
    const result = await client.getPrompt({ name: 'weekly_report', arguments: { days: '14' } });
    expect(result.messages[0]?.content).toMatchObject({ type: 'text', text: expect.stringContaining('last 14 days') });
  });
});

describe('confirmation of destructive tools', () => {
  async function confirming(answer: { action: 'accept' | 'decline'; content?: Record<string, boolean> }) {
    const mcpClient = await connect({ elicitation: { form: {} } });
    const asked: string[] = [];
    mcpClient.setRequestHandler('elicitation/create', async (request) => {
      asked.push((request.params as { message: string }).message);
      return answer;
    });
    return { mcpClient, asked };
  }

  it('runs the action when the user confirms in the client', async () => {
    const { mcpClient, asked } = await confirming({ action: 'accept' });
    const result = await call('terminate_workflow', { workflowId: 12 }, mcpClient);
    expect(result).toMatchObject({ isError: false, data: { success: true } });
    expect(asked[0]).toContain('workflowId: 12');
    expect(fake.lastRequest('/workflows/12')?.method).toBe('DELETE');
    await mcpClient.close();
  });

  it('changes nothing when the user declines', async () => {
    const { mcpClient } = await confirming({ action: 'decline' });
    const result = await call('terminate_workflow', { workflowId: 13 }, mcpClient);
    expect(result.error).toMatchObject({ code: 'cancelled', retryable: false });
    expect(fake.lastRequest('/workflows/13')).toBeUndefined();
    await mcpClient.close();
  });

  it('cancels when the user accepts the form but unticks the confirmation', async () => {
    const { mcpClient } = await confirming({ action: 'accept', content: { confirm: false } });
    expect((await call('terminate_workflow', { workflowId: 16 }, mcpClient)).error).toMatchObject({
      code: 'cancelled',
    });
    expect(fake.lastRequest('/workflows/16')).toBeUndefined();
    await mcpClient.close();
  });

  it('does not ask clients without forms or for non-destructive tools', async () => {
    expect((await call('terminate_workflow', { workflowId: 14 })).isError).toBe(false);
    const { mcpClient, asked } = await confirming({ action: 'decline' });
    expect((await call('resume_workflow', { workflowId: 15 }, mcpClient)).isError).toBe(false);
    expect(asked).toHaveLength(0);
    await mcpClient.close();
  });
});
