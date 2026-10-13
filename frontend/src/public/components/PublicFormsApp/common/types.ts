import { IRuntimeKickoffClient } from '../../../types/template';

export type IPublicFormKickoff = IRuntimeKickoffClient;

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
