export interface IFieldsetTemplateRule {
  apiName: string;
  type: string;
  value: string | null;
  fields: string[];
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
  rules: IFieldsetTemplateRule[];
  fields: IFieldsetField[];
}

export interface IFieldsetBinding extends Omit<IFieldsetCatalogItem, 'id'> {
  sharedFieldsetId: number;
}

export interface IFieldsetBindingClient extends IFieldsetBinding {
  apiNameBinding?: string;
}

export interface IFieldsetBindingMeta {
  sharedFieldsetId: number;
  order: number;
  apiName?: string;
  title?: string;
  description?: string;
}

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
  rules?: Omit<IFieldsetTemplateRule, 'apiName'>[];
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
  rules?: IFieldsetTemplateRule[];
  fields?: IFieldsetField[];
  signal?: AbortSignal;
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
