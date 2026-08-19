import { EExtraFieldType } from '../../../types/template';

export const SINGLE_LINE_FIELD_TYPES = new Set<EExtraFieldType>([
  EExtraFieldType.String,
  EExtraFieldType.Number,
  EExtraFieldType.User,
  EExtraFieldType.Date,
  EExtraFieldType.Url,
]);
