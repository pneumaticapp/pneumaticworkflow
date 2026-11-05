import * as z from 'zod/v4';

import { ConnectorError } from '../core/errors.js';
import { STRING_LIMIT } from '../core/limits.js';

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

export function requireExactlyOne<Args extends object>(args: Args, keys: readonly (keyof Args & string)[]) {
  if (keys.filter((key) => args[key] !== undefined).length !== 1) {
    throw new ConnectorError(
      'invalid_arguments',
      `Provide exactly one of ${keys.slice(0, -1).join(', ')} or ${keys.at(-1)}`,
    );
  }
}
