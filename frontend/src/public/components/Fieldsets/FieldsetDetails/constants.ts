import { EExtraFieldType } from '../../../types/template';
import type { TLocalFieldsetState } from './types';

export const SINGLE_LINE_FIELD_TYPES = new Set<EExtraFieldType>([
  EExtraFieldType.String,
  EExtraFieldType.Number,
  EExtraFieldType.User,
  EExtraFieldType.Date,
  EExtraFieldType.Url,
]);

export const FIELDSET_CHANGE_KEYS: (keyof TLocalFieldsetState)[] = [
  'title',
  'description',
  'labelPosition',
  'fields',
  'rulesets',
];
