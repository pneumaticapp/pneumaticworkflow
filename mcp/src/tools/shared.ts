import type { ToolAnnotations } from '@modelcontextprotocol/server';
import * as z from 'zod/v4';

import { ConnectorError } from '../core/errors.js';
import { isRecord } from '../core/json.js';
import { STRING_LIMIT } from '../core/limits.js';
import type { ToolOutput } from '../mcp/result.js';
import type { PneumaticClient } from '../pneumatic/client.js';
import { forgetPeople, loadPeople } from '../pneumatic/directory.js';
import { Compact } from '../presenters/index.js';

export const readOnly: ToolAnnotations = {
  readOnlyHint: true,
  openWorldHint: false,
};

export const additive: ToolAnnotations = {
  readOnlyHint: false,
  destructiveHint: false,
  idempotentHint: false,
  openWorldHint: false,
};

export const idempotentUpdate: ToolAnnotations = {
  readOnlyHint: false,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
};

export const destructive: ToolAnnotations = {
  readOnlyHint: false,
  destructiveHint: true,
  idempotentHint: true,
  openWorldHint: false,
};

export const id = (entity: string) => z.number().int().positive().describe(`${entity} ID`);

export const idList = (entity: string) => z.array(z.number().int().positive()).describe(`${entity} IDs`);

export const limit = z.number().int().min(1).max(100).default(20).describe('Page size (1-100)');

export const offset = z.number().int().min(0).optional().describe('Number of items to skip');

export const dateTime = z
  .union([z.string(), z.number()])
  .describe('ISO 8601 date-time (e.g. "2026-10-15T09:00:00Z") or Unix timestamp in seconds');

export const fieldValues = z
  .record(z.string(), z.unknown())
  .describe(
    'Map of field api_name to value. Fields inside fieldsets also go at the top level by their own api_name; ' +
      `never use display labels. Value formats by field type: string/text/url -> string (string max ${STRING_LIMIT} chars); ` +
      'number -> number; date -> ISO 8601 date-time (or Unix seconds); radio/dropdown -> one selections value; ' +
      'checkbox -> array of selections values; user -> user email or group name; ' +
      'file -> array of Markdown links "[name](url)" from upload_file (fieldValue) or from fileLinks of a read. ' +
      'A supplied file field replaces its saved files. Field api_names come from get_template_kickoff or get_task.',
  );

export const commentText = z.string().trim().min(1).max(10_000);

export const period = {
  dateFrom: dateTime.optional().describe('Period start; defaults to the start of today'),
  dateTo: dateTime.optional().describe('Period end; defaults to now'),
  currentOnly: z
    .boolean()
    .default(false)
    .describe('true = current snapshot (in progress and overdue only, period ignored; started/completed are null)'),
};

export function toTimestamp(value: string | number): number {
  const invalidDate = () =>
    new ConnectorError('invalid_arguments', `Invalid date-time "${value}". Use ISO 8601, e.g. 2026-10-15T09:00:00Z`);
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) {
      throw invalidDate();
    }
    return Math.abs(value) >= 1e12 ? value / 1000 : value;
  }

  const trimmed = value.trim();
  if (/^-?\d+(\.\d+)?$/.test(trimmed)) {
    return toTimestamp(Number(trimmed));
  }
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(trimmed)) {
    throw invalidDate();
  }
  const year = Number(trimmed.slice(0, 4));
  const month = Number(trimmed.slice(5, 7));
  const day = Number(trimmed.slice(8, 10));
  const isLeapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [31, isLeapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];
  if (!daysInMonth || day < 1 || day > daysInMonth) {
    throw invalidDate();
  }
  const parsed = Date.parse(trimmed);
  if (!Number.isFinite(parsed)) {
    throw invalidDate();
  }
  return parsed / 1000;
}

export function done(): ToolOutput {
  return { data: { success: true } };
}

export async function compactFor(client: PneumaticClient, { people = false } = {}): Promise<Compact> {
  return new Compact({
    appUrl: client.appUrl,
    people: people ? await loadPeople(client).catch(() => undefined) : undefined,
  });
}

export function optionalTimestamp(value: string | number | null | undefined): number | null | undefined {
  return value === undefined || value === null ? value : toTimestamp(value);
}

export function periodQuery(
  dateFrom: string | number | undefined,
  dateTo: string | number | undefined,
  currentOnly: boolean,
) {
  if (currentOnly) {
    return { now: true };
  }
  return { date_from_tsp: optionalTimestamp(dateFrom), date_to_tsp: optionalTimestamp(dateTo) };
}

export function requireExactlyOne<Args extends object>(args: Args, keys: readonly (keyof Args & string)[]) {
  if (keys.filter((key) => args[key] !== undefined).length !== 1) {
    throw new ConnectorError(
      'invalid_arguments',
      `Provide exactly one of ${keys.slice(0, -1).join(', ')} or ${keys.at(-1)}`,
    );
  }
}

export function assignDefined(target: Record<string, unknown>, changes: Record<string, unknown>) {
  for (const [key, value] of Object.entries(changes)) {
    if (value !== undefined) {
      target[key] = value;
    }
  }
}

export async function workflowDetail(client: PneumaticClient, raw: unknown) {
  const compact = await compactFor(client, { people: true });
  return compact.out(compact.workflow(raw, { detail: true }));
}

export async function userDetail(client: PneumaticClient, raw: unknown) {
  // These helpers present the result of a change, so cached names may be stale.
  forgetPeople(client);
  const compact = await compactFor(client);
  return compact.out(compact.user(raw, { detail: true }));
}

export async function fetchTemplate(client: PneumaticClient, templateId: number): Promise<Record<string, unknown>> {
  const raw = await client.get(`/templates/${templateId}`);
  if (raw === null) {
    throw new ConnectorError('not_found', 'The template is inactive and has no saved draft');
  }
  if (!isRecord(raw)) {
    throw new ConnectorError('invalid_response');
  }
  return raw;
}
