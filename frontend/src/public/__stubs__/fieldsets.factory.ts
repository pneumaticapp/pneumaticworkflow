import {
  EFieldLabelPosition, EFieldsetNumberRulesetOperator, IFieldsetBinding, IFieldsetBindingClient, IFieldsetCatalogItem,
  IFieldsetField, IFieldsetRuntime, IFieldsetTaskAPI, IFieldsetRuleSet, IFieldsetRuleGroupAnd, IFieldsetRuleGroupOr,
} from '../types/fieldset';
import { IExtraField } from '../types/template';

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

export const makeFieldsetRuntime = (overrides: Partial<IFieldsetRuntime> = {}): IFieldsetRuntime => ({
  apiNameBinding: 'fs-1',
  name: 'Fieldset 1',
  title: 'Fieldset 1',
  description: '',
  order: 0,
  fields: [],
  labelPosition: EFieldLabelPosition.Top,
  layout: 'vertical',
  ...overrides,
});


export const makeFieldsetRuleGroupAnd = (overrides: Partial<IFieldsetRuleGroupAnd> = {}): IFieldsetRuleGroupAnd => ({
  apiName: 'group-and-1',
  operator: EFieldsetNumberRulesetOperator.SumEqual,
  value: '100',
  ...overrides,
});

export const makeFieldsetRuleGroupOr = (overrides: Partial<IFieldsetRuleGroupOr> = {}): IFieldsetRuleGroupOr => ({
  apiName: 'group-or-1',
  groupsAnd: [makeFieldsetRuleGroupAnd()],
  ...overrides,
});

export const makeFieldsetRuleset = (overrides: Partial<IFieldsetRuleSet> = {}): IFieldsetRuleSet => ({
  apiName: 'rule-1',
  order: 0,
  fields: [],
  groupsOr: [makeFieldsetRuleGroupOr()],
  ...overrides,
});

export const makeFieldsetCatalogItem = (overrides: Partial<IFieldsetCatalogItem> = {}): IFieldsetCatalogItem => ({
  id: 1,
  apiName: 'fs-1',
  name: 'Test Fieldset',
  title: 'Test Fieldset',
  description: '',
  labelPosition: EFieldLabelPosition.Top,
  layout: 'vertical',
  order: 0,
  rulesets: [],
  fields: [],
  usage: [],
  ...overrides,
});

export const makeFieldsetBindingClient = (overrides: Partial<IFieldsetBindingClient> = {}): IFieldsetBindingClient => ({
  sharedFieldsetId: 1,
  apiNameBinding: 'fs-binding-1',
  name: 'Test Fieldset',
  title: 'Test Fieldset',
  description: '',
  labelPosition: EFieldLabelPosition.Top,
  layout: 'vertical',
  order: 0,
  rulesets: [],
  fields: [],
  ...overrides,
});

export const makeFieldsetBinding = (overrides: Partial<IFieldsetBinding> = {}): IFieldsetBinding => ({
  apiName: 'catalog-fs-1',
  sharedFieldsetId: 10,
  name: 'Test Fieldset',
  title: 'Test Fieldset',
  description: '',
  labelPosition: EFieldLabelPosition.Top,
  layout: 'vertical',
  order: 0,
  rulesets: [],
  fields: [],
  ...overrides,
});

export const makeFieldsetTaskAPI = (overrides: Partial<IFieldsetTaskAPI> = {}): IFieldsetTaskAPI => ({
  id: 100,
  apiName: 'task-fs-1',
  name: 'Task Fieldset',
  title: 'Task Fieldset',
  description: '',
  order: 0,
  labelPosition: EFieldLabelPosition.Top,
  layout: 'vertical',
  fields: [] as IExtraField[],
  ...overrides,
});
