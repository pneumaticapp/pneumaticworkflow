export interface IFieldsetTemplateRule {
  id: number;
  type: string;
  value: string;
}

export interface IFieldsetField {
  type: string;
  name: string;
  description?: string;
  is_required?: boolean;
  is_hidden?: boolean;
  selections?: { api_name: string; value: string }[];
  order: number;
  api_name: string;
  default?: string;
  dataset?: number | null;
}

export type TFieldLabelPosition = 'top' | 'left';
export type TFieldSetLayout = 'horizontal' | 'vertical';

export interface IFieldsetTemplate {
  id: number;
  name: string;
  description: string;
  label_position: TFieldLabelPosition;
  layout: TFieldSetLayout;
  order: number;
  rules: IFieldsetTemplateRule[];
  fields: IFieldsetField[];
}

export interface IFieldsetListItem {
  id: number;
  name: string;
  description: string;
  label_position: TFieldLabelPosition;
  layout: TFieldSetLayout;
  order: number;
  rules: IFieldsetTemplateRule[];
  fields: IFieldsetField[];
}

export interface IGetFieldsetsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: IFieldsetListItem[];
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
  description?: string;
  rules?: Omit<IFieldsetTemplateRule, 'id'>[];
  fields?: Omit<IFieldsetField, 'api_name'>[];
}

export interface IUpdateFieldsetParams {
  id: number;
  name?: string;
  description?: string;
  label_position?: TFieldLabelPosition;
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
