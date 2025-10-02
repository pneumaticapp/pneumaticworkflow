/* eslint-disable */
/* prettier-ignore */
import { IKickoff } from '../../../types/template';

export interface IPublicForm {
  accountId: number;
  name: string;
  description: string;
  kickoff: IKickoff;
  showCaptcha: boolean;
}

export enum EPublicFormState {
  Loading = 'loading',
  FormNotFound = 'form-not-found',
  WaitingForAction = 'waiting-for-action',
  Submitting = 'submitting',
  Submitted = 'submitted',
}
