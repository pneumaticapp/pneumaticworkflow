import { ConnectorError } from '../core/errors.js';
import { isFileLink } from '../core/files.js';
import { isRecord, records } from '../core/json.js';
import { STRING_LIMIT } from '../core/limits.js';
import { toTimestamp } from './dates.js';

interface FieldSpec {
  apiName: string;
  name: string;
  type: string;
  isRequired: boolean;
  isHidden: boolean;
  // Dataset options are not always listed in the form, so they cannot be checked.
  hasDataset: boolean;
  selections: string[];
  hasValue: boolean;
}

function selectionValues(values: unknown): string[] {
  return Array.isArray(values)
    ? values
        .map((item) => (isRecord(item) ? item.value : item))
        .filter((value): value is string => typeof value === 'string')
    : [];
}

export function fieldSpecs(fields: unknown, fieldsets: unknown): FieldSpec[] {
  const all = [...records(fields), ...records(fieldsets).flatMap((set) => records(set.fields))];
  return all
    .filter((field) => typeof field.api_name === 'string')
    .map((field) => ({
      apiName: String(field.api_name),
      name: typeof field.name === 'string' ? field.name : String(field.api_name),
      type: typeof field.type === 'string' ? field.type : 'string',
      isRequired: field.is_required === true,
      isHidden: field.is_hidden === true,
      hasDataset: field.dataset !== undefined && field.dataset !== null,
      selections: selectionValues(field.selections),
      hasValue: field.value !== undefined && field.value !== null && field.value !== '',
    }));
}

const isEmpty = (value: unknown) =>
  value === null || value === undefined || value === '' || (Array.isArray(value) && !value.length);

function invalid(field: FieldSpec, problem: string): never {
  throw new ConnectorError('invalid_arguments', `Field "${field.name}" (${field.apiName}): ${problem}`);
}

function oneOf(field: FieldSpec, value: unknown): string {
  if (typeof value !== 'string') {
    invalid(field, 'expected one selections value as a string');
  }
  if (!field.hasDataset && field.selections.length && !field.selections.includes(value)) {
    invalid(field, `"${value}" is not an option; use one of ${JSON.stringify(field.selections)}`);
  }
  return value;
}

function convert(field: FieldSpec, value: unknown): unknown {
  if (isEmpty(value)) {
    return value;
  }
  switch (field.type) {
    case 'date':
      if (typeof value !== 'string' && typeof value !== 'number') {
        invalid(field, 'expected an ISO 8601 date-time or Unix seconds');
      }
      try {
        return toTimestamp(value);
      } catch {
        return invalid(field, 'expected an ISO 8601 date-time with time and offset, e.g. 2027-01-15T09:00:00Z');
      }
    case 'number':
      if (!Number.isFinite(Number(value)) || typeof value === 'boolean') {
        invalid(field, 'expected a number');
      }
      return value;
    case 'radio':
    case 'dropdown':
      return oneOf(field, value);
    case 'checkbox':
      return (Array.isArray(value) ? value : [value]).map((item) => oneOf(field, item));
    case 'file': {
      // Pneumatic drops blank items, so they are not errors.
      const links = (Array.isArray(value) ? value : [value]).filter(
        (link) => !(typeof link === 'string' && !link.trim()),
      );
      if (!links.every((link) => typeof link === 'string' && isFileLink(link.trim()))) {
        invalid(field, 'expected an array of "[name](url)" links from upload_file (fieldValue) or fileLinks');
      }
      return links;
    }
    case 'string':
      if (typeof value !== 'string') {
        invalid(field, 'expected a string');
      }
      // Pneumatic counts characters (code points), not UTF-16 units.
      if ([...value].length > STRING_LIMIT) {
        invalid(field, `string fields hold at most ${STRING_LIMIT} characters; use a text field for longer values`);
      }
      return value;
    default:
      if (typeof value !== 'string') {
        invalid(field, 'expected a string');
      }
      return value;
  }
}

export interface PrepareOptions {
  checkRequired: 'all' | 'unfilled' | 'none';
}

export function prepareFieldValues(
  specs: FieldSpec[],
  values: Record<string, unknown> = {},
  { checkRequired }: PrepareOptions,
): Record<string, unknown> {
  const byApiName = new Map(specs.map((field) => [field.apiName, field]));
  const unknown = Object.keys(values).filter((key) => !byApiName.has(key));
  if (unknown.length) {
    const hints = unknown.map((key) => {
      const label = specs.find((field) => field.name.toLowerCase() === key.toLowerCase());
      return label ? `"${key}" is a label; use api_name "${label.apiName}"` : `"${key}" is unknown`;
    });
    throw new ConnectorError(
      'invalid_arguments',
      `${hints.join('; ')}. Known fields: ${specs.map((field) => `${field.apiName} (${field.name}, ${field.type})`).join(', ')}`,
    );
  }
  const prepared = Object.fromEntries(
    Object.entries(values).map(([key, value]) => [key, convert(byApiName.get(key)!, value)]),
  );
  if (checkRequired !== 'none') {
    const missing = specs.filter((field) => {
      // Hidden fields are filled by integrations, not by the performer.
      if (!field.isRequired || field.isHidden) {
        return false;
      }
      if (field.apiName in prepared) {
        return isEmpty(prepared[field.apiName]);
      }
      return checkRequired === 'all' || !field.hasValue;
    });
    if (missing.length) {
      throw new ConnectorError(
        'invalid_arguments',
        `Required fields are empty: ${missing.map((field) => `${field.apiName} (${field.name})`).join(', ')}`,
      );
    }
  }
  return prepared;
}
