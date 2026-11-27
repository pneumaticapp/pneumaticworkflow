import * as z from 'zod/v4';

import { ConnectorError } from '../core/errors.js';
import { isRecord } from '../core/json.js';
import { tool, type ToolDef } from '../mcp/toolDef.js';
import { additive, readOnly } from './annotations.js';
import { templateDetail } from './details.js';
import { present } from './output.js';
import { id, limit, offset } from './schemas.js';
import { chainInOrder, sortedTasks } from './templateSteps.js';

export const libraryTools: ToolDef[] = [
  tool(
    'generate_template_steps',
    {
      title: 'Generate template steps with AI',
      description:
        "Ask Pneumatic's AI to propose process steps for a description (admins only; the AI feature must be " +
        'enabled on the Pneumatic server and counts against the account AI limit). Nothing is created: review the ' +
        'steps with the user, then pass them to create_template.',
      inputSchema: z.strictObject({
        description: z.string().trim().min(1).max(500).describe('What the process is about'),
      }),
      annotations: { ...additive, openWorldHint: true },
    },
    async ({ description }, { client }) => {
      const raw = await client.post('/templates/ai', { description });
      if (!isRecord(raw)) {
        throw new ConnectorError('invalid_response');
      }
      return present(client, (presenter) => ({
        ...presenter.pick(raw, ['name']),
        steps: presenter.objects(raw.tasks, (task) =>
          presenter.pick(task, ['number', 'name', 'description'], ['description']),
        ),
      }));
    },
  ),

  tool(
    'list_library_templates',
    {
      title: 'List library templates',
      description:
        'Search the Pneumatic template library (ready-made processes) with pagination (admins only). Use ' +
        'create_template_from_library to add one to the account. withCategories=true also returns the categories.',
      inputSchema: z.strictObject({
        search: z.string().max(200).optional(),
        categoryId: id('Library category').optional(),
        withCategories: z.boolean().default(false),
        limit,
        offset,
      }),
      annotations: readOnly,
    },
    async ({ search, categoryId, withCategories, limit, offset }, { client }) => {
      const raw = await client.get('/templates/system', { search, category: categoryId, limit, offset });
      const categories = withCategories ? await client.get('/templates/system/categories') : undefined;
      return present(client, (presenter) => ({
        ...presenter.page(raw, { limit, offset }, (item) =>
          presenter.pick(item, ['id', 'name', 'description', 'category']),
        ),
        ...(withCategories
          ? { categories: presenter.objects(categories, (item) => presenter.pick(item, ['id', 'name'])) }
          : {}),
      }));
    },
  ),

  tool(
    'create_template_from_library',
    {
      title: 'Create template from library',
      description:
        'Add a library template to the account (admins only). The connected user becomes the owner and the ' +
        'performer of steps without performers. Steps run one after another unless sequential=false. Saved as an ' +
        'inactive draft unless isActive=true. Repeating the call creates another template.',
      inputSchema: z.strictObject({
        libraryTemplateId: id('Library template'),
        sequential: z.boolean().default(true),
        isActive: z.boolean().default(false),
      }),
      annotations: additive,
    },
    async ({ libraryTemplateId, sequential, isActive }, { client }) => {
      const body = await client.post(`/templates/system/${libraryTemplateId}/fill`);
      if (!isRecord(body) || !Array.isArray(body.tasks)) {
        throw new ConnectorError('invalid_response');
      }
      const tasks = sortedTasks(body);
      // Library steps that already carry conditions of any kind keep them; only unconditioned templates are chained.
      if (sequential && !tasks.some((task) => Array.isArray(task.conditions) && task.conditions.length)) {
        chainInOrder(tasks);
      }
      return templateDetail(client, await client.post('/templates', { ...body, is_active: isActive }));
    },
  ),
];
