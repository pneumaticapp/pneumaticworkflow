import { Client, InMemoryTransport } from '@modelcontextprotocol/client';

import { loadConfig } from '../src/config.js';
import { createClientFactory } from '../src/pneumatic/client.js';
import { buildServer } from '../src/server.js';

if (process.env.SMOKE_WRITES !== 'yes') {
  console.error('Refusing to run: set SMOKE_WRITES=yes and use an API key of a disposable Pneumatic account.');
  process.exit(2);
}

const config = loadConfig(['--stdio']);
if (config.transport !== 'stdio') {
  throw new Error('stdio configuration expected');
}
const server = buildServer(createClientFactory(config)(config.apiKey));
const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
const client = new Client({ name: 'smoke-write', version: '1.0.0' });
await server.connect(serverTransport);
await client.connect(clientTransport);

type Data = Record<string, any>;
let failures = 0;

async function call(name: string, args: Record<string, unknown> = {}): Promise<Data> {
  const result = await client.callTool({ name, arguments: args });
  const content = result.structuredContent as { data?: Data; error?: { code: string; detail?: string } } | undefined;
  if (result.isError || !content?.data) {
    throw new Error(content?.error ? `${content.error.code}: ${content.error.detail ?? ''}` : 'invalid tool result');
  }
  return content.data;
}

function need<T>(value: T | undefined | null, what: string): T {
  if (value === undefined || value === null || value === '') {
    throw new Error(`missing ${what}`);
  }
  return value;
}

async function step<T>(name: string, run: () => Promise<T>): Promise<T | undefined> {
  try {
    const value = await run();
    console.log(`PASS ${name}`);
    return value;
  } catch (error) {
    failures += 1;
    console.log(`FAIL ${name}: ${error instanceof Error ? error.message.slice(0, 300) : 'unknown error'}`);
    return undefined;
  }
}

let templateId: number | undefined;
let workflowId: number | undefined;

try {
  const template = await step('create_template', () =>
    call('create_template', {
      name: `Connector smoke ${new Date().toISOString()}`,
      kickoffFields: [{ name: 'Request', type: 'string', isRequired: true }],
      steps: [
        {
          name: 'Review',
          checklist: ['Read the request'],
          fields: [
            { name: 'Decision', type: 'dropdown', selections: ['Approve', 'Reject'], isRequired: true },
            { name: 'Attachment', type: 'file' },
          ],
        },
        { name: 'Archive' },
      ],
    }),
  );
  templateId = template?.id;

  const requestField = templateId
    ? await step('get_template_kickoff', async () =>
        need((await call('get_template_kickoff', { templateId })).fields?.[0]?.apiName as string, 'kickoff apiName'),
      )
    : undefined;

  const workflow = requestField
    ? await step('run_workflow', async () => {
        const data = await call('run_workflow', {
          templateId,
          name: 'Connector smoke run',
          kickoff: { [requestField]: 'Smoke test' },
        });
        need(data.id, 'workflow id');
        need(
          data.tasks?.find((task: Data) => task.status === 'active'),
          'an active task in the result',
        );
        return data;
      })
    : undefined;
  workflowId = workflow?.id;
  const taskId = workflow?.tasks?.find((task: Data) => task.status === 'active')?.id as number | undefined;

  const task = taskId
    ? await step('get_task', async () => {
        const data = await call('get_task', { taskId });
        need(data.checklists?.[0]?.selections?.[0]?.id, 'a checklist item');
        for (const name of ['Decision', 'Attachment']) {
          need(data.output?.find((field: Data) => field.name === name)?.apiName, `output field ${name}`);
        }
        return data;
      })
    : undefined;
  const fields = new Map<string, string>((task?.output ?? []).map((field: Data) => [field.name, field.apiName]));
  const decision = fields.get('Decision');
  const attachment = fields.get('Attachment');

  if (task && decision && attachment) {
    const checklist = task.checklists[0];
    await step('set_checklist_item', () =>
      call('set_checklist_item', { checklistId: checklist.id, selectionId: checklist.selections[0].id, checked: true }),
    );
    const upload = config.filesUrl
      ? await step('upload_file', async () => {
          const data = await call('upload_file', { filename: 'smoke.txt', contentText: 'Connector smoke test' });
          need(data.fieldValue, 'fieldValue');
          return data;
        })
      : undefined;
    await step('comment_on_task', () =>
      call('comment_on_task', { taskId, text: `Smoke comment${upload ? ` with ${upload.fieldValue}` : ''}` }),
    );
    await step('complete_task (field checks reject a bad option)', async () => {
      const result = await client.callTool({
        name: 'complete_task',
        arguments: { taskId, output: { [decision]: 'Maybe' } },
      });
      const error = (result.structuredContent as { error?: { detail?: string } } | undefined)?.error;
      if (!result.isError || !error?.detail?.includes('is not an option')) {
        throw new Error('an invalid option was not rejected by the field checks');
      }
    });
    await step('complete_task', () =>
      call('complete_task', {
        taskId,
        output: { [decision]: 'Approve', ...(upload ? { [attachment]: [upload.fieldValue] } : {}) },
      }),
    );
  }

  if (workflowId) {
    await step('get_workflow (next step active)', async () => {
      const current = await call('get_workflow', { workflowId });
      if (!current.tasks?.some((item: Data) => item.name === 'Archive' && item.status === 'active')) {
        throw new Error('the second step did not start');
      }
    });
    await step('snooze_workflow', () =>
      call('snooze_workflow', { workflowId, until: new Date(Date.now() + 86_400_000).toISOString() }),
    );
    await step('resume_workflow', () => call('resume_workflow', { workflowId }));
  }
} finally {
  if (workflowId) {
    await step('cleanup: terminate_workflow', () => call('terminate_workflow', { workflowId }));
  }
  if (templateId) {
    await step('cleanup: delete_template', () => call('delete_template', { templateId }));
  }
  await client.close();
}

console.log(failures ? `${failures} step(s) failed` : 'All write steps passed');
process.exit(failures ? 1 : 0);
