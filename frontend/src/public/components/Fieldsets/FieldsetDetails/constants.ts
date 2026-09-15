import { EExtraFieldType } from '../../../types/template';
import { EFieldLabelPosition } from '../../../types/fieldset';
import { TLocalFieldsetState } from './types';

export const SINGLE_LINE_FIELD_TYPES = new Set<EExtraFieldType>([
  EExtraFieldType.String,
  EExtraFieldType.Number,
  EExtraFieldType.User,
  EExtraFieldType.Date,
  EExtraFieldType.Url,
]);

export const EMPTY_LOCAL_FIELDSET: TLocalFieldsetState = {
  title: '',
  description: '',
  labelPosition: EFieldLabelPosition.Top,
  fields: [],
  rulesets: [],
};
