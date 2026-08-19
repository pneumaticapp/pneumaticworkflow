import type { IExtraField } from './template';

export enum EFieldsetNumberRulesetOperator {
  SumEqual = 'sum_equal',
  SumGreaterThan = 'sum_greater_than',
  SumLessThan = 'sum_less_than',
}

export interface IFieldsetRuleGroupAnd {
  apiName: string;
  operator: EFieldsetNumberRulesetOperator;
  value: string;
}

export interface IFieldsetRuleGroupOr {
  apiName: string;
  groupsAnd: IFieldsetRuleGroupAnd[];
}

export interface IFieldsetRuleSet {
  apiName: string;
  message?: string | null;
  order: number;
  fields: string[];
  groupsOr: IFieldsetRuleGroupOr[];
}

export interface IFieldsetField {
  type: string;
  name: string;
  description?: string;
  isRequired?: boolean;
  isHidden?: boolean;
  selections?: { apiName: string; value: string }[];
  order: number;
  apiName: string;
  default?: string;
  dataset?: number | null;
}

export enum EFieldLabelPosition {
  Top = 'top',
  Left = 'left',
}
export type TFieldSetLayout = 'horizontal' | 'vertical';

export interface IFieldsetCatalogItem {
  id: number;
  apiName: string;
  name: string;
  description: string;
  labelPosition: EFieldLabelPosition;
  layout: TFieldSetLayout;
  order: number;
  title: string;
  rulesets?: IFieldsetRuleSet[];
  fields: IFieldsetField[];
  usage: { id: number; name: string }[];
}

export interface IFieldsetBinding extends Omit<IFieldsetCatalogItem, 'id' | 'usage'> {
  sharedFieldsetId: number;
}

export interface IFieldsetBindingClient extends Omit<IFieldsetBinding, 'apiName'> {
  apiNameBinding: string;
}

export interface IFieldsetRuntime extends Omit<IFieldsetBindingClient, 'fields' | 'sharedFieldsetId' | 'rulesets'> {
  fields: IExtraField[];
}

export interface IFieldsetTaskAPI {
  id: number;
  apiName: string;
  name: string;
  description: string;
  order: number;
  labelPosition: EFieldLabelPosition;
  layout: TFieldSetLayout;
  title: string;
  fields: IExtraField[];
}

export type IFieldsetBindingMeta = Omit<IFieldsetBindingClient, 'apiNameBinding'> & {
  apiName?: string;
};

export interface IGetFieldsetsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: IFieldsetCatalogItem[];
}

export interface IGetFieldsetsParams {
  ordering?: string;
  limit?: number;
  offset?: number;
  signal?: AbortSignal;
}

export interface IGetFieldsetParams {
  id: number;
  signal?: AbortSignal;
}

export interface ICreateFieldsetParams {
  name: string;
  apiName?: string;
  title?: string;
  description?: string;
  order?: number;
  labelPosition?: EFieldLabelPosition;
  layout?: TFieldSetLayout;
  rulesets?: Omit<IFieldsetRuleSet, 'apiName'>[];
  fields?: Omit<IFieldsetField, 'apiName'>[];
}

export interface IUpdateFieldsetParams {
  id: number;
  name?: string;
  apiName?: string;
  description?: string;
  order?: number;
  title?: string;
  labelPosition?: EFieldLabelPosition;
  layout?: TFieldSetLayout;
  rulesets?: IFieldsetRuleSet[];
  fields?: IFieldsetField[];
  signal?: AbortSignal;
  onSuccess?: () => void;
}

export interface IDeleteFieldsetParams {
  id: number;
}

export enum EFieldsetsSorting {
  DateDesc = 'date-desc',
  DateAsc = 'date-asc',
  NameAsc = 'name-asc',
  NameDesc = 'name-desc',
}
