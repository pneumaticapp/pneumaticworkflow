import { APIRequestContext } from '@playwright/test';
import { BACKEND_API_URL, getBearerToken } from './types';

export async function deleteTestTemplate(request: APIRequestContext, templateId: number): Promise<void> {
  const response = await request.delete(`${BACKEND_API_URL}/templates/${templateId}`, {
    headers: { Authorization: `Bearer ${getBearerToken()}` },
  });

  if (!response.ok() && response.status() !== 404) {
    throw new Error(`deleteTestTemplate: failed to delete template ${templateId}. Status: ${response.status()}`);
  }
}
