import type { IFieldsetBinding } from './fieldset';
import type { IExtraField, IExtraFieldSelectionAPI, IRuntimeKickoffClient } from './template';

export type TPublicFormType = 'shared' | 'embedded';

export type IPublicFormKickoff = IRuntimeKickoffClient;

export interface IPublicForm {
  accountId: number;
  name: string;
  description: string;
  kickoff: IPublicFormKickoff;
  showCaptcha: boolean;
}

export interface IPublicFormFieldResponse extends Omit<IExtraField, 'selections'> {
  selections?: IExtraFieldSelectionAPI[] | string[];
}

export interface IPublicFormFieldsetResponse extends Omit<IFieldsetBinding, 'fields'> {
  fields: IPublicFormFieldResponse[];
}

export interface IPublicFormKickoffResponse extends Omit<IPublicFormKickoff, 'fields' | 'fieldsets'> {
  fields: IPublicFormFieldResponse[];
  fieldsets: IPublicFormFieldsetResponse[];
}

export interface IPublicFormResponse extends Omit<IPublicForm, 'kickoff'> {
  kickoff: IPublicFormKickoffResponse;
}
