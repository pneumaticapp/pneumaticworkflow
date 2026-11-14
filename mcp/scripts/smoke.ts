import { loadConfig } from '../src/config.js';
import { createPneumaticClient, PneumaticApiError, type Query } from '../src/pneumatic/client.js';

const config = loadConfig(['--stdio']);
if (config.transport !== 'stdio') {
  throw new Error('stdio configuration expected');
}
const client = createPneumaticClient(config.pneumatic, config.apiKey);
const checks: Array<[string, string, Query?]> = [
  ['get_current_user', '/accounts/user'],
  ['list_users', '/accounts/users', { limit: 1 }],
  ['list_groups', '/accounts/groups', { limit: 1 }],
  ['list_templates', '/templates', { limit: 1 }],
  ['list_workflows', '/workflows', { limit: 1 }],
  ['list_tasks', '/v3/tasks', { is_completed: false, limit: 1 }],
  ['get_dashboard', '/reports/dashboard/workflows/overview'],
  ['list_highlights', '/reports/highlights', { limit: 1 }],
  ['list_datasets', '/datasets', { limit: 1 }],
  ['list_attachments', '/attachments', { limit: 1 }],
];

for (const [name, path, query] of checks) {
  try {
    await client.get(path, query);
    console.log(`${name}: OK`);
  } catch (error) {
    if (error instanceof PneumaticApiError) {
      throw new Error(`${name}: Pneumatic returned HTTP ${error.status}`);
    }
    throw error;
  }
}
