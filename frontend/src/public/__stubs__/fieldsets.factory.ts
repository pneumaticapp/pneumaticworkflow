import { EFieldLabelPosition, IFieldsetTemplate, IFieldsetListItem } from '../types/fieldset';
import { IFieldsetData } from '../types/template';

export const makeFieldsetData = (overrides: Partial<IFieldsetData> = {}): IFieldsetData => ({
  id: 1,
  apiName: 'fs-1',
  name: 'Fieldset 1',
  description: '',
  order: 0,
  fields: [],
  labelPosition: EFieldLabelPosition.Top,
  rulesCount: 0,
  ...overrides,
});

export const makeFieldsetTemplate = (overrides: Partial<IFieldsetTemplate> = {}): IFieldsetTemplate => ({
  id: 1,
  name: 'Fieldset Template',
  description: '',
  labelPosition: EFieldLabelPosition.Top,
  layout: 'vertical',
  order: 0,
  kickoffId: null,
  taskId: null,
  rules: [],
  fields: [],
  ...overrides,
});

export const makeFieldsetListItem = (overrides: Partial<IFieldsetListItem> = {}): IFieldsetListItem => ({
  id: 1,
  apiName: 'fs-1',
  name: 'Test Fieldset',
  description: '',
  labelPosition: EFieldLabelPosition.Top,
  layout: 'vertical',
  order: 0,
  kickoffId: null,
  taskId: null,
  rules: [],
  fields: [],
  ...overrides,
});
