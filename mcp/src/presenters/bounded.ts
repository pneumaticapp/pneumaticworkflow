import { ConnectorError } from '../core/errors.js';
import { isRecord } from '../core/json.js';

export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
export type JsonObject = { [key: string]: Json };

const MAX_NESTED_ITEMS = 100;
const MAX_GENERIC_ITEMS = 20;
const MAX_PRIMITIVE_ITEMS = 1000;
const MAX_GENERIC_DEPTH = 4;
const MAX_STRING_BYTES = 2048;
const MAX_LONG_TEXT_BYTES = 8192;
const TEXT_BUDGET_BYTES = 32 * 1024;

// Only prose shares the text budget: identifiers, enums and file links must stay intact to be reusable in writes.
const FREE_TEXT_KEYS = new Set(['description', 'text', 'value', 'default']);

export interface PageArgs {
  limit: number;
  offset?: number;
}

const camel = (key: string) => key.replace(/_([a-z0-9])/g, (_, char: string) => char.toUpperCase());

export function isoDate(seconds: unknown): Json {
  // Date supports ±8.64e15 ms; anything outside is a broken value and must not fail the whole result.
  return typeof seconds === 'number' && Math.abs(seconds) <= 8.64e12 ? new Date(seconds * 1000).toISOString() : null;
}

export function pageResults(raw: unknown): unknown[] {
  const results = Array.isArray(raw) ? raw : isRecord(raw) ? raw.results : undefined;
  if (!Array.isArray(results)) {
    throw new ConnectorError('invalid_response');
  }
  return results;
}

function utf8Slice(value: string, maxBytes: number): string {
  return Buffer.from(value, 'utf8').subarray(0, maxBytes).toString('utf8').replace(/�+$/, '');
}

export class BoundedJson {
  truncated = false;
  private textBudget = TEXT_BUDGET_BYTES;

  out(data: Json) {
    return { data, truncated: this.truncated };
  }

  text(value: unknown, maxBytes = MAX_STRING_BYTES): Json {
    if (typeof value !== 'string') {
      return this.value(value);
    }
    const size = Buffer.byteLength(value, 'utf8');
    const maximum = Math.max(0, Math.min(maxBytes, this.textBudget));
    this.textBudget -= Math.min(size, maximum);
    return this.slice(value, size, maximum);
  }

  private slice(value: string, size: number, maximum: number): string {
    if (size > maximum) {
      this.truncated = true;
      return utf8Slice(value, maximum);
    }
    return value;
  }

  value(value: unknown, depth = 0): Json {
    if (value === undefined || value === null) {
      return null;
    }
    if (typeof value === 'string') {
      return this.slice(value, Buffer.byteLength(value, 'utf8'), MAX_STRING_BYTES);
    }
    if (typeof value === 'number') {
      return Number.isFinite(value) ? value : null;
    }
    if (typeof value === 'boolean') {
      return value;
    }
    if (Array.isArray(value)) {
      const primitive = value.every((item) => item === null || typeof item !== 'object');
      const maxItems = primitive ? MAX_PRIMITIVE_ITEMS : MAX_GENERIC_ITEMS;
      if (value.length > maxItems || (value.length && depth >= MAX_GENERIC_DEPTH)) {
        this.truncated = true;
      }
      return depth < MAX_GENERIC_DEPTH ? value.slice(0, maxItems).map((item) => this.value(item, depth + 1)) : [];
    }
    if (isRecord(value)) {
      const entries = Object.entries(value);
      if (entries.length > MAX_GENERIC_ITEMS || (entries.length && depth >= MAX_GENERIC_DEPTH)) {
        this.truncated = true;
      }
      if (depth >= MAX_GENERIC_DEPTH) {
        return {};
      }
      return Object.fromEntries(
        entries.slice(0, MAX_GENERIC_ITEMS).map(([key, item]) => [key, this.value(item, depth + 1)]),
      );
    }
    return null;
  }

  protected requireRecord(value: unknown): Record<string, unknown> {
    if (!isRecord(value)) {
      throw new ConnectorError('invalid_response');
    }
    return value;
  }

  pick(value: unknown, keys: readonly string[], longKeys: readonly string[] = []): JsonObject {
    const record = this.requireRecord(value);
    const data: JsonObject = {};
    for (const key of keys) {
      if (!(key in record)) {
        continue;
      }
      const value = record[key];
      if (key.endsWith('_tsp')) {
        // Models misread Unix seconds; ISO 8601 is also what the date-time tool inputs accept.
        data[camel(key.slice(0, -4))] = isoDate(value);
      } else if (longKeys.includes(key)) {
        data[camel(key)] = this.text(value, MAX_LONG_TEXT_BYTES);
      } else if (FREE_TEXT_KEYS.has(key)) {
        data[camel(key)] = this.text(value);
      } else {
        data[camel(key)] = this.value(value);
      }
    }
    return data;
  }

  objects(values: unknown, converter: (item: unknown) => Json, maxItems = MAX_NESTED_ITEMS): Json[] {
    if (values === undefined || values === null) {
      return [];
    }
    if (!Array.isArray(values)) {
      throw new ConnectorError('invalid_response');
    }
    if (values.length > maxItems) {
      this.truncated = true;
    }
    return values.slice(0, maxItems).map(converter);
  }

  page(raw: unknown, { limit, offset = 0 }: PageArgs, converter: (item: unknown) => Json): JsonObject {
    const results = pageResults(raw);
    const total = isRecord(raw) && typeof raw.count === 'number' ? raw.count : null;
    const items = this.objects(results.slice(0, limit), converter);
    const end = offset + items.length;
    const hasMore = total === null ? items.length === limit : end < total;
    return {
      items,
      page: { limit, offset, returned: items.length, total, nextOffset: hasMore ? end : null },
    };
  }
}
