import { isRecord } from '../core/json.js';
import type { Json, JsonObject, PageArgs } from './bounded.js';

export const MAX_RESULT_BYTES = 64 * 1024;

// Cutting a file field's links would make a resubmission silently delete the omitted files.
const UNCUTTABLE_LISTS = new Set(['fileLinks']);

export interface Envelope {
  data: Json;
  truncated: boolean;
}

interface Candidate {
  list: Json[];
  minLength: number;
}

function findLists(value: Json, candidates: Candidate[], key = '', root = false): void {
  if (Array.isArray(value)) {
    const minLength = root ? 1 : 0;
    if (value.length > minLength && !UNCUTTABLE_LISTS.has(key)) {
      candidates.push({ list: value, minLength });
    }
    for (const child of value) {
      findLists(child, candidates);
    }
  } else if (value && typeof value === 'object') {
    for (const [childKey, child] of Object.entries(value)) {
      findLists(child, candidates, childKey);
    }
  }
}

const byteSize = (value: unknown) => Buffer.byteLength(JSON.stringify(value), 'utf8');

// Measuring lists without their nested lists cuts the list that owns the bulk, not always the outermost one.
const ownSize = (list: Json[]) =>
  Buffer.byteLength(
    JSON.stringify(list, (key, value) => (key !== '' && Array.isArray(value) ? [] : value)),
    'utf8',
  );

export function boundEnvelope(envelope: Envelope): Envelope {
  const { data } = envelope;
  const items = isRecord(data) && Array.isArray(data.items) ? data.items : undefined;
  const pageLength = items?.length;
  while (byteSize(envelope) > MAX_RESULT_BYTES) {
    const candidates: Candidate[] = [];
    if (isRecord(data)) {
      for (const [key, child] of Object.entries(data)) {
        findLists(child, candidates, key, child === items);
      }
    } else {
      findLists(data, candidates, '', true);
    }
    envelope.truncated = true;
    if (!candidates.length) {
      envelope.data = isRecord(data)
        ? Object.fromEntries(Object.entries(data).filter(([, value]) => value === null || typeof value !== 'object'))
        : null;
      break;
    }
    // Halving every list of comparable size per pass keeps the loop logarithmic for many sibling lists.
    const sizes = candidates.map(({ list }) => ownSize(list));
    const threshold = sizes.reduce((max, size) => Math.max(max, size), 0) / 2;
    candidates.forEach(({ list, minLength }, index) => {
      if ((sizes[index] ?? 0) >= threshold) {
        list.splice(Math.max(minLength, Math.floor(list.length / 2)));
      }
    });
  }
  if (items && isRecord(data) && isRecord(data.page) && items.length !== pageLength) {
    const page = data.page as JsonObject;
    page.returned = items.length;
    page.nextOffset = Number(page.offset ?? 0) + items.length;
  }
  return envelope;
}

// Some endpoints return every row at once; cut the requested page locally.
export function localPage(raw: unknown, { limit, offset = 0 }: PageArgs): unknown {
  return Array.isArray(raw) ? { count: raw.length, results: raw.slice(offset, offset + limit) } : raw;
}
