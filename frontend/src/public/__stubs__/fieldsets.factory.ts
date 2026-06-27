import {
  EFieldLabelPosition, IFieldsetBindingClient, IFieldsetCatalogItem, IFieldsetField, IFieldsetTemplateRule,
} from '../types/fieldset';
import { IFieldsetData } from '../types/template';

export const makeFieldsetField = (overrides: Partial<IFieldsetField> = {}): IFieldsetField => ({
  apiName: 'field-1',
  name: 'Field 1',
  description: '',
  type: 'string',
  isRequired: false,
  isHidden: false,
  order: 0,
  default: '',
  dataset: null,
  selections: [],
  ...overrides,
});

export const makeFieldsetData = (overrides: Partial<IFieldsetData> = {}): IFieldsetData => ({
  sharedFieldsetId: 1,
  apiNameBinding: 'fs-1',
  name: 'Fieldset 1',
  description: '',
  order: 0,
  fields: [],
  labelPosition: EFieldLabelPosition.Top,
  rulesCount: 0,
  ...overrides,
});


export const makeFieldsetTemplateRule = (overrides: Partial<IFieldsetTemplateRule> = {}): IFieldsetTemplateRule => ({
  apiName: 'rule-1',
  type: 'sum_equal',
  value: '100',
  fields: [],
  ...overrides,
});

export const makeFieldsetCatalogItem = (overrides: Partial<IFieldsetCatalogItem> = {}): IFieldsetCatalogItem => ({
  id: 1,
  apiName: 'fs-1',
  name: 'Test Fieldset',
  description: '',
  labelPosition: EFieldLabelPosition.Top,
  layout: 'vertical',
  order: 0,
  title: '',
  rules: [],
  fields: [],
  ...overrides,
});

export const makeFieldsetBindingClient = (overrides: Partial<IFieldsetBindingClient> = {}): IFieldsetBindingClient => ({
  sharedFieldsetId: 1,
  apiNameBinding: 'fs-binding-1',
  name: 'Test Fieldset',
  description: '',
  labelPosition: EFieldLabelPosition.Top,
  layout: 'vertical',
  order: 0,
  title: '',
  rules: [],
  fields: [],
  ...overrides,
});
