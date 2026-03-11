import { APIRequestContext } from '@playwright/test';
import { BACKEND_API_URL, getBearerToken } from './types';

export async function resetTemplateFields(request: APIRequestContext, templateId: number): Promise<void> {
  const headers = { Authorization: `Bearer ${getBearerToken()}` };

  const getResponse = await request.get(`${BACKEND_API_URL}/templates/${templateId}`, { headers });
  if (!getResponse.ok()) {
    throw new Error(`resetTemplateFields: GET failed. Status: ${getResponse.status()}`);
  }

  const template = (await getResponse.json()) as {
    kickoff?: { fields?: Array<Record<string, unknown>> };
    tasks?: Array<{ fields?: Array<Record<string, unknown>> }>;
  };

  const resetField = (f: Record<string, unknown>) => ({
    ...f,
    isRequired: false,
    isHidden: false,
    is_required: false,
    is_hidden: false,
  });

  if (template.kickoff?.fields) {
    template.kickoff.fields = template.kickoff.fields.map(resetField);
  }
  if (template.tasks) {
    template.tasks = template.tasks.map((task) => ({
      ...task,
      fields: (task.fields ?? []).map(resetField),
    }));
  }

  const putResponse = await request.put(`${BACKEND_API_URL}/templates/${templateId}`, {
    data: template,
    headers,
  });
  if (!putResponse.ok()) {
    throw new Error(`resetTemplateFields: PUT failed. Status: ${putResponse.status()}`);
  }
}
