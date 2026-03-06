import { APIRequestContext } from '@playwright/test';
import { BACKEND_API_URL, getBearerToken } from './types';
import { EExtraFieldType } from '../../src/public/types/template';
import { ICreateTemplateOptions, ICreatedTemplate, TFieldType } from './types';

export async function createTestTemplate(
  request: APIRequestContext,
  options: ICreateTemplateOptions = {},
): Promise<ICreatedTemplate> {
  const { kickoffFields = 0, taskFields = 0, defaultFieldType = EExtraFieldType.Text } = options;

  const suffix = Date.now();

  const normalizeFieldTypes = (input: number | TFieldType[]): TFieldType[] =>
    typeof input === 'number' ? Array.from({ length: input }, () => defaultFieldType) : input;

  const kickoffTypes = normalizeFieldTypes(kickoffFields);
  const taskTypes = normalizeFieldTypes(taskFields);

  const kickoffFieldsData = kickoffTypes.map((type, i) => ({
    apiName: `kickoff-field-${i + 1}-${suffix}`,
    name: `Kickoff field ${i + 1} (${type})`,
    type,
    order: i + 1,
    isRequired: false,
    isHidden: false,
    userId: null,
    groupId: null,
  }));

  const taskFieldsData = taskTypes.map((type, i) => ({
    apiName: `task-field-${i + 1}-${suffix}`,
    name: `Task field ${i + 1} (${type})`,
    type,
    order: i + 1,
    isRequired: false,
    isHidden: false,
    userId: null,
    groupId: null,
  }));

  const body = {
    name: `E2E test template ${suffix}`,
    description: '',
    isActive: true,
    finalizable: false,
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
    isEmbedded: false,
    embedUrl: null,
    wfNameTemplate: null,
    owners: [],
    kickoff: {
      description: '',
      fields: kickoffFieldsData,
    },
    tasks: [
      {
        apiName: `task-1-${suffix}`,
        number: 1,
        name: 'Task 1',
        description: '',
        delay: null,
        requireCompletionByAll: false,
        rawPerformers: [],
        fields: taskFieldsData,
        conditions: [],
        checklists: [],
        revertTask: null,
        ancestors: [],
        rawDueDate: null,
      },
    ],
  };

  const ctxResponse = await request.get(`${BACKEND_API_URL}/auth/context`, {
    headers: { Authorization: `Bearer ${getBearerToken()}` },
  });
  const ctx = (await ctxResponse.json()) as { id: number };
  const userId = ctx.id;

  const response = await request.post(`${BACKEND_API_URL}/templates`, {
    data: {
      ...body,
      tasks: body.tasks.map((t) => ({
        ...t,
        rawPerformers: [{ type: 'user', sourceId: userId }],
      })),
    },
    headers: { Authorization: `Bearer ${getBearerToken()}` },
  });

  if (!response.ok()) {
    throw new Error(
      `createTestTemplate: failed to create template. Status: ${response.status()}\n${await response.text()}`,
    );
  }

  const json = (await response.json()) as {
    id: number;
    kickoff: { fields: Array<{ apiName: string; name: string }> };
    tasks: Array<{ fields: Array<{ apiName: string; name: string }> }>;
  };

  return {
    templateId: json.id,
    kickoffFields: (json.kickoff?.fields ?? []).map((f) => ({ apiName: f.apiName, name: f.name })),
    taskFields: (json.tasks?.[0]?.fields ?? []).map((f) => ({ apiName: f.apiName, name: f.name })),
  };
}
