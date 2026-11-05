import * as z from 'zod/v4';

import { ConnectorError } from '../core/errors.js';
import { records } from '../core/json.js';
import { id } from './schemas.js';
import type { RawTask } from './templateSteps.js';

const FIELD_TYPES = [
  'string',
  'text',
  'radio',
  'checkbox',
  'date',
  'url',
  'dropdown',
  'file',
  'user',
  'number',
] as const;
const SELECTION_TYPES = new Set(['radio', 'checkbox', 'dropdown']);

export const field = z.strictObject({
  name: z.string().trim().min(1).max(200),
  type: z.enum(FIELD_TYPES),
  description: z.string().max(2000).optional(),
  isRequired: z.boolean().optional().describe('user fields are always required'),
  selections: z.array(z.string().min(1).max(200)).max(500).optional().describe('Options for radio/checkbox/dropdown'),
  datasetId: id('Dataset').optional().describe('Dataset with the options for radio/checkbox/dropdown'),
});

export const performer = z.strictObject({
  type: z.enum(['user', 'group', 'workflowStarter']),
  id: id('User or group').optional().describe('User or group ID; omit for workflowStarter'),
});

export const step = z.strictObject({
  name: z.string().trim().min(1).max(280),
  description: z.string().max(5000).optional(),
  performers: z.array(performer).min(1).max(50).optional().describe('Defaults to the connected user'),
  fields: z.array(field).max(50).optional().describe('Output fields the performer fills in'),
  checklist: z.array(z.string().trim().min(1).max(2000)).max(100).optional().describe('Checklist items'),
  dueInHours: z
    .number()
    .positive()
    .max(24 * 365)
    .optional()
    .describe('Due date relative to the task start'),
  requireCompletionByAll: z.boolean().optional().describe('All performers must complete the task'),
});

type FieldInput = z.infer<typeof field>;
type StepInput = z.infer<typeof step>;

export function fieldPayload(fields: FieldInput[] = []) {
  // The frontend shows fields in descending `order`.
  return fields.map((item, index) => {
    if (SELECTION_TYPES.has(item.type) && !item.selections?.length && item.datasetId === undefined) {
      throw new ConnectorError(
        'invalid_arguments',
        `Field "${item.name}" of type ${item.type} needs selections or datasetId`,
      );
    }
    return {
      name: item.name,
      type: item.type,
      order: fields.length - index,
      description: item.description ?? '',
      is_required: item.type === 'user' ? true : (item.isRequired ?? false),
      ...(item.selections ? { selections: item.selections.map((value) => ({ value })) } : {}),
      ...(item.datasetId === undefined ? {} : { dataset: item.datasetId }),
    };
  });
}

// Existing fields keep their api names and order; new ones go below every field and fieldset of the form.
export function appendFields(current: unknown, add: FieldInput[] = [], fieldsets: unknown = []) {
  const fields = records(current);
  if (!add.length) {
    return fields;
  }
  const orders = [...fields, ...records(fieldsets)].map((item) => Number(item.order)).filter(Number.isFinite);
  const lowest = orders.length ? Math.min(...orders) : add.length + 1;
  return [...fields, ...fieldPayload(add).map((item, index) => ({ ...item, order: lowest - 1 - index }))];
}

export function performerPayload(performers: NonNullable<StepInput['performers']>) {
  return performers.map(({ type, id: sourceId }) => {
    if (type === 'workflowStarter') {
      return { type: 'workflow_starter', source_id: null };
    }
    if (sourceId === undefined) {
      throw new ConnectorError('invalid_arguments', `A ${type} performer needs an id`);
    }
    return { type, source_id: sourceId };
  });
}

export function formatDuration(hours: number): string {
  const totalMinutes = Math.max(1, Math.ceil(hours * 60));
  const days = Math.floor(totalMinutes / (24 * 60));
  const rest = totalMinutes - days * 24 * 60;
  const time = `${String(Math.floor(rest / 60)).padStart(2, '0')}:${String(rest % 60).padStart(2, '0')}:00`;
  return days ? `${days} ${time}` : time;
}

export function checklistPayload(items: string[]) {
  return items.length ? [{ selections: items.map((value) => ({ value })) }] : [];
}

export function dueDatePayload(hours: number, taskApiName: string) {
  return { duration: formatDuration(hours), duration_months: 0, rule: 'after task started', source_id: taskApiName };
}

export function taskPayload(item: StepInput, taskApiName: string, currentUser: number): RawTask & { api_name: string } {
  return {
    name: item.name,
    api_name: taskApiName,
    description: item.description ?? '',
    require_completion_by_all: item.requireCompletionByAll ?? false,
    raw_performers: performerPayload(item.performers ?? [{ type: 'user', id: currentUser }]),
    fields: fieldPayload(item.fields),
    checklists: checklistPayload(item.checklist ?? []),
    raw_due_date: item.dueInHours === undefined ? null : dueDatePayload(item.dueInHours, taskApiName),
  };
}
