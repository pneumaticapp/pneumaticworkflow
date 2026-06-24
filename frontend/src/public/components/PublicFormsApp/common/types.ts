import { IKickoffClient, IFieldsetData } from '../../../types/template';

export interface IPublicFormKickoff extends Omit<IKickoffClient, 'fieldsets'> {
  fieldsets: IFieldsetData[];
}

export interface IPublicForm {
  accountId: number;
  name: string;
  description: string;
  kickoff: IPublicFormKickoff;
  showCaptcha: boolean;
}

export enum EPublicFormState {
  Loading = 'loading',
  FormNotFound = 'form-not-found',
  WaitingForAction = 'waiting-for-action',
  Submitting = 'submitting',
  Submitted = 'submitted',
}
