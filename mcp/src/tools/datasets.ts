import * as z from 'zod/v4';

import type { PneumaticClient } from '../pneumatic/client.js';

import { tool, type ToolDef } from '../mcp/toolDef.js';
import { ConnectorError } from '../core/errors.js';
import { isRecord, records } from '../core/json.js';
import { compactFor, additive, destructive, done, id, limit, offset, readOnly } from './shared.js';

const datasetId = id('Dataset');
const itemValue = z.string().trim().min(1).max(200);

async function datasetDetail(client: PneumaticClient, raw: unknown) {
  const compact = await compactFor(client);
  return compact.out({
    ...compact.pick(raw, ['id', 'name', 'description']),
    items: compact.objects(isRecord(raw) ? raw.items : undefined, (item) => compact.pick(item, ['id', 'value']), 1000),
  });
}

export const datasetReadTools: ToolDef[] = [
  tool(
    'list_datasets',
    {
      title: 'List datasets',
      description: 'List datasets: reusable option lists that feed dropdown, radio and checkbox fields.',
      inputSchema: z.strictObject({ limit, offset }),
      annotations: readOnly,
    },
    async ({ limit, offset }, { client }) => {
      const compact = await compactFor(client);
      const raw = await client.get('/datasets', { limit, offset });
      return compact.out(
        compact.page(raw, { limit, offset }, (item) =>
          compact.pick(item, ['id', 'name', 'description', 'items_count', 'date_created_tsp']),
        ),
      );
    },
  ),

  tool(
    'get_dataset',
    {
      title: 'Get dataset',
      description: 'Get a dataset with all its items (option values).',
      inputSchema: z.strictObject({ datasetId }),
      annotations: readOnly,
    },
    async ({ datasetId }, { client }) => datasetDetail(client, await client.get(`/datasets/${datasetId}`)),
  ),
];

export const datasetTools: ToolDef[] = [
  tool(
    'create_dataset',
    {
      title: 'Create dataset',
      description:
        'Create a dataset (option list for dropdown, radio and checkbox fields) with its items (admins only). ' +
        'Dataset names are unique in the account and item values are unique in a dataset.',
      inputSchema: z.strictObject({
        name: z.string().trim().min(1).max(200),
        description: z.string().max(2000).optional(),
        items: z.array(itemValue).max(1000).optional(),
      }),
      annotations: additive,
    },
    async ({ name, description, items = [] }, { client }) =>
      datasetDetail(
        client,
        await client.post('/datasets', {
          name,
          description: description ?? '',
          items: items.map((value, order) => ({ value, order })),
        }),
      ),
  ),

  tool(
    'update_dataset',
    {
      title: 'Update dataset',
      description:
        'Rename a dataset, change its description, and add, rename or remove items by value (admins only). ' +
        'Removed options disappear from fields that use the dataset. All changes are checked before any is ' +
        'written. Returns the updated dataset.',
      inputSchema: z.strictObject({
        datasetId,
        name: z.string().trim().min(1).max(200).optional(),
        description: z.string().max(2000).optional(),
        addItems: z.array(itemValue).max(1000).optional(),
        renameItems: z
          .array(z.strictObject({ from: itemValue, to: itemValue }))
          .max(1000)
          .optional(),
        removeItems: z.array(itemValue).max(1000).optional(),
      }),
      annotations: destructive,
    },
    async ({ datasetId, name, description, addItems = [], renameItems = [], removeItems = [] }, { client }) => {
      const current = await client.get(`/datasets/${datasetId}`);
      const items = isRecord(current) ? records(current.items) : [];
      // Validate the whole change set first: the API applies item changes one call at a time.
      const idOf = (value: string) => {
        const item = items.find((candidate) => candidate.value === value);
        if (!item) {
          throw new ConnectorError('invalid_arguments', `The dataset has no item "${value}"`);
        }
        return item.id;
      };
      const renames = renameItems.map(({ from, to }) => ({ itemId: idOf(from), to }));
      const removals = removeItems.map(idOf);
      const finalValues = new Set(items.map((item) => String(item.value)));
      removeItems.forEach((value) => finalValues.delete(value));
      for (const { from, to } of renameItems) {
        finalValues.delete(from);
        if (finalValues.has(to)) {
          throw new ConnectorError('invalid_arguments', `The dataset already has an item "${to}"`);
        }
        finalValues.add(to);
      }
      for (const value of addItems) {
        if (finalValues.has(value)) {
          throw new ConnectorError('invalid_arguments', `The dataset already has an item "${value}"`);
        }
        finalValues.add(value);
      }
      if (name !== undefined || description !== undefined) {
        await client.patch(`/datasets/${datasetId}`, { name, description });
      }
      for (const { itemId, to } of renames) {
        await client.patch(`/datasets/items/${itemId}`, { value: to });
      }
      for (const itemId of removals) {
        await client.delete(`/datasets/items/${itemId}`);
      }
      if (addItems.length) {
        const maxOrder = Math.max(-1, ...items.map((item) => Number(item.order) || 0));
        await client.post(
          `/datasets/${datasetId}/items`,
          addItems.map((value, index) => ({ value, order: maxOrder + 1 + index })),
        );
      }
      return datasetDetail(client, await client.get(`/datasets/${datasetId}`));
    },
  ),

  tool(
    'delete_dataset',
    {
      title: 'Delete dataset',
      description: 'Delete a dataset (admins only). Fields that use it lose their options.',
      inputSchema: z.strictObject({ datasetId }),
      annotations: destructive,
    },
    async ({ datasetId }, { client }) => {
      await client.delete(`/datasets/${datasetId}`);
      return done();
    },
  ),
];
