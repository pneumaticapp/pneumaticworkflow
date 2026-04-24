export interface IFieldsetTemplateRule {
  id: number;
  type: string;
  value: string;
  fields: string[];
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
  labelPosition: TFieldLabelPosition;
  layout: TFieldSetLayout;
  order: number;
  kickoffId: number | null;
  taskId: number | null;
  rules: IFieldsetTemplateRule[];
  fields: IFieldsetField[];
}

export interface IFieldsetListItem {
  id: number;
  name: string;
  description: string;
  labelPosition: TFieldLabelPosition;
  layout: TFieldSetLayout;
  order: number;
  kickoffId: number | null;
  taskId: number | null;
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
  templateId: number;
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
  templateId: number;
  name: string;
  description?: string;
  rules?: Omit<IFieldsetTemplateRule, 'id'>[];
  fields?: Omit<IFieldsetField, 'api_name'>[];
}

export interface IUpdateFieldsetParams {
  id: number;
  name?: string;
  description?: string;
  order?: number;
  kickoff_id?: number | null;
  task_id?: number | null;
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
