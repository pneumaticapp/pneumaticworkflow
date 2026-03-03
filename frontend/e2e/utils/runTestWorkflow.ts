import { APIRequestContext } from '@playwright/test';
import { BACKEND_API_URL, getBearerToken } from './types';

export async function runTestWorkflow(request: APIRequestContext, templateId: number): Promise<number> {
  const response = await request.post(`${BACKEND_API_URL}/templates/${templateId}/run`, {
    data: { name: `E2E run ${Date.now()}` },
    headers: { Authorization: `Bearer ${getBearerToken()}` },
  });

  if (!response.ok()) {
    throw new Error(
      `runTestWorkflow: failed to run workflow for template ${templateId}. Status: ${response.status()}\n${await response.text()}`,
    );
  }

  const json = (await response.json()) as { tasks: Array<{ id: number }> };
  const taskId = json.tasks?.[0]?.id;
  if (!taskId) {
    throw new Error(`runTestWorkflow: response has no tasks[0].id`);
  }

  return taskId;
}
