import { EExtraFieldType, IExtraField } from '../types/template';

export const makeExtraField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
  apiName: 'field-1',
  name: 'Field',
  type: EExtraFieldType.String,
  order: 0,
  userId: null,
  groupId: null,
  description: '',
  isRequired: false,
  isHidden: false,
  value: '',
  selections: [],
  attachments: [],
  dataset: null,
  ...overrides,
});
